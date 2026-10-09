"""Source-clock beat/pitch evidence and explicit, invertible musical anchors.

Run heavy commands with the locked audio environment. JSON clocks and tests use
only the standard library. Estimates remain estimates until reviewed in audio.
"""

import argparse
import bisect
import importlib.metadata
import itertools
import json
import math
import os
import subprocess
import time
from pathlib import Path

from candidate_evidence import build_evidence
from runtime import digest, write_json


def positive_number(value, name, zero=False):
    if not isinstance(value, (float, int)) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric")
    if not math.isfinite(value) or value < 0 or (not zero and value == 0):
        raise ValueError(f"invalid {name}")
    return value


class BeatClock:
    """Interpolate reviewed anchors; never silently extrapolate or snap notes."""

    def __init__(self, anchors):
        if len(anchors) < 2:
            raise ValueError("at least two anchors are required")
        self.seconds = [positive_number(a["seconds"], "seconds", True) for a in anchors]
        self.beats = [positive_number(a["beat"], "beat", True) for a in anchors]
        for axis in (self.seconds, self.beats):
            if any(b <= a for a, b in itertools.pairwise(axis)):
                raise ValueError("anchors must strictly increase on both axes")

    @staticmethod
    def interpolate(value, source, target):
        positive_number(value, "position", True)
        if value < source[0] or value > source[-1]:
            raise ValueError("position outside anchored interval")
        i = min(bisect.bisect_right(source, value) - 1, len(source) - 2)
        fraction = (value - source[i]) / (source[i + 1] - source[i])
        return target[i] + fraction * (target[i + 1] - target[i])

    def to_beats(self, seconds):
        return self.interpolate(seconds, self.seconds, self.beats)

    def to_seconds(self, beat):
        return self.interpolate(beat, self.beats, self.seconds)


def fit_pulse(beats, bpm, origin=0):
    """Diagnose a proposed constant pulse, retaining missed/half-time beats.

    The rounded indices identify pulse cycles, not score note positions. This
    reports evidence for a clock hypothesis and never modifies candidate notes.
    """
    import numpy as np

    positive_number(bpm, "bpm")
    positive_number(origin, "origin", True)
    values = np.asarray(beats, dtype=float)
    if len(values) < 3 or not np.all(np.isfinite(values)):
        raise ValueError("at least three finite beat detections are required")
    if np.any(values < 0) or np.any(np.diff(values) <= 0):
        raise ValueError("beat detections must be nonnegative and increasing")
    indices = np.rint((values - origin) * bpm / 60)
    keep = np.ones(len(values), dtype=bool)
    slope, intercept = 60 / bpm, origin
    for _ in range(4):
        if keep.sum() < 3 or np.ptp(indices[keep]) == 0:
            raise ValueError("insufficient distinct pulse cycles")
        slope, intercept = np.polyfit(indices[keep], values[keep], 1)
        residual = values - (intercept + slope * indices)
        median = np.median(residual[keep])
        scale = max(0.02, 3 * 1.4826 * np.median(abs(residual[keep] - median)))
        keep = abs(residual - median) <= scale
    residual = values - (intercept + slope * indices)
    return {
        "hypothesis_bpm": bpm,
        "hypothesis_origin_seconds": origin,
        "fitted_bpm": float(60 / slope),
        "fitted_origin_seconds": float(intercept),
        "beat_count": len(values),
        "fit_fraction": float(np.mean(keep)),
        "all_residual_median_ms": float(np.median(abs(residual)) * 1000),
        "all_residual_p95_ms": float(np.quantile(abs(residual), 0.95) * 1000),
        "residual_seconds": residual.tolist(),
        "pulse_indices": indices.astype(int).tolist(),
        "review_status": "estimated",
    }


def read_audio(path, start=0, duration=None):
    import librosa
    import numpy as np
    import soundfile as sf

    positive_number(start, "start", True)
    info = sf.info(path)
    if duration is None:
        duration = info.duration - start
    positive_number(duration, "duration")
    if start + duration > info.duration + 1 / info.samplerate:
        raise ValueError("requested excerpt extends beyond audio")
    audio, rate = sf.read(
        path,
        start=round(start * info.samplerate),
        frames=round(duration * info.samplerate),
        always_2d=True,
        dtype="float32",
    )
    # Select one channel for F0/beat inference so antiphase stereo is not erased.
    channel = int(np.argmax(np.mean(audio**2, axis=0)))
    mono = librosa.resample(audio[:, channel], orig_sr=rate, target_sr=16000)
    return mono, {
        "sample_rate": 16000,
        "selected_channel": channel,
        "start": start,
        "duration": len(audio) / rate,
        "source_sha256": digest(path),
    }


def beats_command(args):
    import torch
    from beat_this.inference import Audio2Beats

    torch.set_num_threads(4)
    audio, metadata = read_audio(args.input, args.start, args.duration)
    tracker = Audio2Beats(checkpoint_path=args.model, device="cpu", dbn=False)
    beats, downbeats = tracker(audio, metadata["sample_rate"])
    checkpoint = (
        Path(torch.hub.get_dir()) / "checkpoints" / f"beat_this-{args.model}.ckpt"
    )
    return {
        **metadata,
        "model": args.model,
        "review_status": "estimated",
        "package_version": importlib.metadata.version("beat-this"),
        "checkpoint_sha256": digest(checkpoint),
        "beats": (beats + args.start).tolist(),
        "downbeats": (downbeats + args.start).tolist(),
    }


def pitch_command(args):
    import librosa
    import numpy as np

    audio, metadata = read_audio(args.input, args.start, args.duration)
    if not 0 <= args.lowest < args.highest <= 127:
        raise ValueError("pitch bounds must satisfy 0 <= lowest < highest <= 127")
    if args.method != "pyin":
        from melody_backend import estimate_pitch

        matrix_path = args.output.with_suffix(".npz")
        if matrix_path.exists():
            raise ValueError("pitch score matrix output must be new")
        result, matrix = estimate_pitch(
            audio,
            args.method,
            os.environ["TRANSCRIPTION_RUNTIME"],
            args.device,
            args.lowest,
            args.highest,
        )
        result["times"] = [t + args.start for t in result["times"]]
        matrix["times"] += args.start
        np.savez_compressed(matrix_path, **matrix)
        return {
            **metadata,
            **result,
            "score_matrix": matrix_path.name,
            "score_matrix_sha256": digest(matrix_path),
            "lowest": args.lowest,
            "highest": args.highest,
        }
    frame = 4096 if args.lowest < 45 else 2048
    f0, voiced, probability = librosa.pyin(
        audio,
        sr=16000,
        frame_length=frame,
        hop_length=160,
        fmin=librosa.midi_to_hz(args.lowest),
        fmax=librosa.midi_to_hz(args.highest),
    )
    pitch = librosa.hz_to_midi(f0)
    return {
        **metadata,
        "method": "pYIN",
        "hop_seconds": 0.01,
        "package_version": importlib.metadata.version("librosa"),
        "frame_length": frame,
        "review_status": "estimated",
        "lowest": args.lowest,
        "highest": args.highest,
        "times": (np.arange(len(f0)) * 0.01 + args.start).tolist(),
        "pitch": [float(p) if math.isfinite(p) else None for p in pitch],
        "voiced": voiced.tolist(),
        "voiced_probability": probability.tolist(),
    }


def acoustic_agreement(song, evidence, channels, offset=0):
    """Compare a Go sidecar with voiced F0 frames; this is not note accuracy.

    Coverage is reported separately so silence, empty candidates or an empty
    voicing estimate cannot masquerade as an accurate transcription.
    """
    if not math.isfinite(offset):
        raise ValueError("source offset must be finite")
    if not channels or any(c not in range(1, 17) or c == 10 for c in channels):
        raise ValueError("select explicit pitched melody channels")
    times, pitches, probabilities = (
        evidence[k] for k in ("times", "pitch", "voiced_probability")
    )
    if not (len(times) == len(pitches) == len(probabilities)):
        raise ValueError("evidence arrays differ in length")
    if any(b <= a for a, b in itertools.pairwise(times)):
        raise ValueError("evidence times must increase")
    notes = [
        n
        for part in song["parts"]
        if part["channel"] in channels
        for n in part.get("notes", [])
    ]
    count, covered, exact, octave, expanded = 0, 0, 0, 0, 0
    active_predictions, supported_predictions = 0, 0
    for t, pitch, probability in zip(times, pitches, probabilities, strict=True):
        positive_number(t, "frame time", True)
        positive_number(probability, "voiced probability", True)
        if probability > 1:
            raise ValueError("voiced probability exceeds one")
        if pitch is None or probability < 0.8:
            continue
        positive_number(pitch, "pitch", True)
        count += 1
        active = [
            n for n in notes if n["start_seconds"] <= t + offset < n["end_seconds"]
        ]
        near = [
            n
            for n in notes
            if n["start_seconds"] - 0.1 <= t + offset < n["end_seconds"] + 0.1
        ]
        covered += bool(active)
        active_predictions += len(active)
        supported_predictions += sum(abs(n["pitch"] - pitch) <= 0.5 for n in active)
        exact += any(abs(n["pitch"] - pitch) <= 0.5 for n in active)
        octave += any(abs((n["pitch"] - pitch + 6) % 12 - 6) <= 0.5 for n in active)
        expanded += any(abs(n["pitch"] - pitch) <= 0.5 for n in near)

    def ratio(value):
        return value / count if count else None

    return {
        "metric_scope": "estimated voiced-frame agreement; not reference-note accuracy",
        "review_status": "estimated",
        "channels": sorted(channels),
        "source_offset_seconds": offset,
        "candidate_notes": len(notes),
        "total_audio_frames": len(times),
        "confident_voiced_frames": count,
        "voiced_frame_fraction": count / len(times) if times else None,
        "active_frame_coverage": ratio(covered),
        "pitch_frame_agreement": ratio(exact),
        "pitch_class_frame_agreement": ratio(octave),
        "pitch_agreement_with_100ms_margin": ratio(expanded),
        "active_note_pitch_support": supported_predictions / active_predictions
        if active_predictions
        else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("beats", "pitch", "game"):
        p = sub.add_parser(name)
        p.add_argument("input", type=Path)
        p.add_argument("output", type=Path)
        p.add_argument("--start", type=float, default=0)
        p.add_argument("--duration", type=float)
        if name == "beats":
            p.add_argument("--model", choices=("small0", "final0"), default="small0")
        elif name == "game":
            p.add_argument(
                "--language", choices=("auto", "en", "ja", "yue", "zh"), default="auto"
            )
        else:
            p.add_argument(
                "--method", choices=("pyin", "rmvpe", "crepe"), default="pyin"
            )
            p.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
            p.add_argument("--lowest", type=int, default=48)
            p.add_argument("--highest", type=int, default=88)
    p = sub.add_parser("pulse")
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--bpm", type=float, required=True)
    p.add_argument("--origin", type=float, default=0)
    p = sub.add_parser("agreement", help="diagnostic F0 coverage, not accuracy/PASS")
    p.add_argument("input", type=Path, help="Go-generated song.json")
    p.add_argument("pitch", type=Path, help="pitch command JSON")
    p.add_argument("output", type=Path)
    p.add_argument("--channels", required=True, help="comma-separated melody channels")
    p.add_argument("--source-offset", type=float, default=0)
    p = sub.add_parser(
        "evidence", help="phrase candidates and native scores, not corrections"
    )
    p.add_argument("input", type=Path, help="version 1 evidence manifest")
    p.add_argument("output", type=Path)
    p = sub.add_parser(
        "assist", help="optional audio-model opinion with a bounded API budget"
    )
    p.add_argument("input", type=Path, help="version 1 audio review job")
    p.add_argument("output", type=Path)
    p.add_argument("--provider", choices=("antigravity", "openrouter"), required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--ledger", type=Path)
    p.add_argument("--budget-usd", type=float, default=5)
    args = parser.parse_args()
    if (
        args.output.exists()
        or args.output.is_symlink()
        or args.output.resolve() == args.input.resolve()
    ):
        parser.error("output must be a new file distinct from input")
    started = time.monotonic()
    try:
        if args.command == "assist":
            from audio_assist import assist

            result = assist(args)
        elif args.command == "game":
            from game_backend import game_command

            result = game_command(args, Path(os.environ["TRANSCRIPTION_RUNTIME"]))
        elif args.command == "evidence":
            result = build_evidence(args.input)
        elif args.command == "pulse":
            source = json.loads(args.input.read_text())
            result = fit_pulse(source["beats"], args.bpm, args.origin)
            result["input_sha256"] = digest(args.input)
        elif args.command == "agreement":
            result = acoustic_agreement(
                json.loads(args.input.read_text()),
                json.loads(args.pitch.read_text()),
                {int(c) for c in args.channels.split(",")},
                args.source_offset,
            )
            result.update(
                input_sha256=digest(args.input), pitch_sha256=digest(args.pitch)
            )
        else:
            result = (
                beats_command(args) if args.command == "beats" else pitch_command(args)
            )
        result["elapsed_seconds"] = time.monotonic() - started
        write_json(args.output, result)
    except (
        ValueError,
        TypeError,
        OSError,
        KeyError,
        subprocess.TimeoutExpired,
    ) as error:
        parser.exit(2, f"{error}\n")
    print(args.output)


if __name__ == "__main__":
    main()
