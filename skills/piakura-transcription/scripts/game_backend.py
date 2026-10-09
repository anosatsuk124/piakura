"""GAME note proposals and native scores; the agent authors the SakuraMML score.

The ONNX `scores` output is a fractional MIDI pitch, not confidence. Observation
outputs expose native sigmoids without changing graph nodes or model weights.
"""

import hashlib
import json
import math
from pathlib import Path

from runtime import digest

VERSION = "1.0.3"
ARCHIVE_SHA256 = "8a5480539fe7d995800dc0efe149b83a1cd4f4e4a36aa2a1f7665f1765dcac08"
LANGUAGES = {"auto": 0, "en": 1, "ja": 2, "yue": 3, "zh": 4}


def segments_from_arrays(durations, presence, pitches, valid, origin=0):
    if not math.isfinite(origin) or origin < 0:
        raise ValueError("invalid source origin")
    lengths = {len(v) for v in (durations, presence, pitches, valid)}
    if len(lengths) != 1:
        raise ValueError("inconsistent note axes")
    cursor, segments, padding = origin, [], False
    for duration, voiced, pitch, keep in zip(
        durations, presence, pitches, valid, strict=True
    ):
        if not keep:
            padding = True
            continue
        if padding:
            raise ValueError("note padding must be trailing")
        duration, pitch = float(duration), float(pitch)
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("invalid note duration")
        if not math.isfinite(pitch) or (voiced and not 0 <= pitch <= 127):
            raise ValueError("invalid note pitch")
        segments.append(
            {
                "id": len(segments),
                "start_seconds": cursor,
                "end_seconds": cursor + duration,
                "presence": bool(voiced),
                "pitch_semitones": pitch if voiced else None,
                "nearest_midi_pitch": math.floor(pitch + 0.5) if voiced else None,
                "calibrated_probability": None,
            }
        )
        # Unvoiced regions occupy time too. Dropping them shifts later notes.
        cursor += duration
    return segments


class GameModel:
    def __init__(self, runtime, seed=47):
        import onnx
        import onnxruntime as ort
        from onnx import TensorProto, helper

        root = Path(runtime) / "models/game" / VERSION
        source = root / f"GAME-{VERSION}-large-onnx"
        manifest = json.loads((root / "source.json").read_text())
        if manifest["archive_sha256"] != ARCHIVE_SHA256:
            raise ValueError("unexpected GAME checkpoint")
        for name, expected in manifest["files"].items():
            if digest(source / name) != expected:
                raise ValueError(f"modified GAME input: {name}")
        self.config = json.loads((source / "config.json").read_text())
        if self.config["timestep"] != 0.01 or self.config["samplerate"] != 44100:
            raise ValueError("unexpected GAME clock")
        ort.disable_telemetry_events()
        ort.set_seed(seed)
        self.sessions, graphs = {}, {}
        for name in ("encoder", "dur2bd", "segmenter", "bd2dur", "estimator"):
            path = source / f"{name}.onnx"
            model = onnx.load(path)
            if name in ("segmenter", "estimator"):
                sigmoid = [n for n in model.graph.node if n.op_type == "Sigmoid"]
                if len(sigmoid) != 1:
                    raise ValueError("unexpected GAME observation graph")
                shape = ["B", "T"] if name == "segmenter" else ["B", "N", 257]
                for output in (sigmoid[0].input[0], sigmoid[0].output[0]):
                    model.graph.output.append(
                        helper.make_tensor_value_info(output, TensorProto.FLOAT, shape)
                    )
            onnx.checker.check_model(model)
            serialized = model.SerializeToString()
            graphs[name] = hashlib.sha256(serialized).hexdigest()
            options = ort.SessionOptions()
            options.intra_op_num_threads, options.inter_op_num_threads = 4, 1
            self.sessions[name] = ort.InferenceSession(
                serialized, sess_options=options, providers=["CPUExecutionProvider"]
            )
        self.metadata = {
            "model": f"GAME-{VERSION}-large",
            "archive_sha256": ARCHIVE_SHA256,
            "runtime_version": ort.__version__,
            "seed": seed,
            "observation_graph_sha256": graphs,
            "score_semantics": "native uncalibrated sigmoid; pitch bins are Gaussian-blurred targets",
            "duration_semantics": "model note regions, not measured piano key-down durations",
            "license": "CC-BY-NC-SA-4.0",
        }

    def call(self, name, **inputs):
        return self.sessions[name].run(None, inputs)

    def predict(self, audio, language="auto", origin=0):
        import numpy as np

        if language not in LANGUAGES or not 0 < len(audio) <= 30 * 44100:
            raise ValueError("use a supported language and an excerpt up to 30 seconds")
        duration = np.array([len(audio) / 44100], dtype="float32")
        xseg, xest, mask = self.call("encoder", waveform=audio[None], duration=duration)
        (known,) = self.call("dur2bd", durations=duration[:, None], maskT=mask)
        boundaries, history, logits = known.copy(), [], []
        for t in np.linspace(0, 1, 9, dtype="float32")[:-1]:
            boundaries, raw, scores = self.call(
                "segmenter",
                x_seg=xseg,
                language=np.array([LANGUAGES[language]], dtype="int64"),
                known_boundaries=known,
                prev_boundaries=boundaries,
                t=np.array([t], dtype="float32"),
                maskT=mask,
                threshold=np.array(0.2, dtype="float32"),
                radius=np.array(2, dtype="int64"),
            )
            history.append(scores[0])
            logits.append(raw[0])
        durations, nmask = self.call("bd2dur", boundaries=boundaries, maskT=mask)
        presence, pitches, note_logits, note_scores = self.call(
            "estimator",
            x_est=xest,
            boundaries=boundaries,
            maskT=mask,
            maskN=nmask,
            threshold=np.array(0.2, dtype="float32"),
        )
        segments = segments_from_arrays(
            durations[0], presence[0], pitches[0], nmask[0], origin
        )
        return {
            **self.metadata,
            "language": language,
            "steps": 8,
            "boundary_threshold": 0.2,
            "presence_threshold": 0.2,
            "segments": segments,
            "review_status": "raw proposals; musical review required",
        }, {
            "times": np.arange(mask.shape[1])[mask[0]] * 0.01 + origin,
            "boundary_score": history[-1][mask[0]],
            "boundary_history": np.array(history)[:, mask[0]],
            "boundary_logits": np.array(logits)[:, mask[0]],
            "note_times": np.array(
                [(s["start_seconds"] + s["end_seconds"]) / 2 for s in segments]
            ),
            # Keep native out-of-MIDI-range bins separately; phrase packets
            # accept only MIDI 0..127 and must not reinterpret bin 128.
            "raw_note_pitch_bins": np.arange(257) * 0.5,
            "raw_note_pitch_scores": note_scores[0, nmask[0]],
            "note_pitch_bins": np.arange(255) * 0.5,
            "note_pitch_scores": note_scores[0, nmask[0], :255],
            "note_pitch_logits": note_logits[0, nmask[0]],
        }


def game_command(args, runtime):
    import librosa
    import numpy as np
    import soundfile as sf
    from audio_review import positive_number

    positive_number(args.start, "start", True)
    info = sf.info(args.input)
    duration = (
        args.duration if args.duration is not None else info.duration - args.start
    )
    positive_number(duration, "duration")
    if duration > 30 or args.start + duration > info.duration + 1 / info.samplerate:
        raise ValueError("use an available excerpt of at most 30 seconds")
    evidence = args.output.with_suffix(".npz")
    if evidence == args.output or evidence.exists() or evidence.is_symlink():
        raise ValueError("evidence output already exists")
    audio, rate = sf.read(
        args.input,
        start=round(args.start * info.samplerate),
        frames=round(duration * info.samplerate),
        dtype="float32",
        always_2d=True,
    )
    channel = int(np.argmax(np.mean(audio * audio, axis=0)))
    waveform = librosa.resample(audio[:, channel], orig_sr=rate, target_sr=44100)
    model = GameModel(runtime)
    result, arrays = model.predict(waveform, args.language, args.start)
    evidence.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(evidence, **arrays)
    return {
        **result,
        "source_sha256": digest(args.input),
        "selected_channel": channel,
        "start": args.start,
        "duration": len(audio) / rate,
        "evidence_sha256": digest(evidence),
    }
