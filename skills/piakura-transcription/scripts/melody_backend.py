"""Pinned vocal model adapters with native score arrays and explicit clocks.

Upstream ROSVOT's CLI requires CUDA even for one input. These adapters invoke
its unchanged model/feature modules on the requested device, retaining logits
that the stock CLI discards. Musical reconstruction remains in SakuraMML.
"""

import importlib.metadata
import json
import math
import sys
from pathlib import Path

from runtime import digest, write_json

REVISION = "3c8332bf43adae35f6e4d64971862f2f6139b310"


def source_directory(runtime):
    source = Path(runtime) / "models/rosvot" / REVISION
    manifest = json.loads((source / "source.json").read_text())
    if manifest["revision"] != REVISION:
        raise ValueError("unexpected ROSVOT revision")
    for name, expected in manifest["files"].items():
        if digest(source / name) != expected:
            raise ValueError(f"modified ROSVOT input: {name}")
    sys.path.insert(0, str(source))
    return source


def initialize():
    import numpy as np
    import torch

    torch.set_num_threads(4)
    torch.manual_seed(0)
    np.random.seed(0)


def pitch_bins():
    import numpy as np

    frequency = 10 * 2 ** ((20 * np.arange(360) + 1997.3794084376191) / 1200)
    return 69 + 12 * np.log2(frequency / 440)


def crepe_frequency_bounds(lowest, highest):
    # Upstream converts fmin to a slice index without clamping. Piano A0
    # becomes a negative index and masks almost every useful pitch bin.
    low = max(32.0, 440 * 2 ** ((lowest - 69) / 12))
    high = min(2006.0, 440 * 2 ** ((highest - 69) / 12))
    if not low < high:
        raise ValueError(
            "requested pitch range does not overlap CREPE's supported range"
        )
    return low, high


def decode_crepe_scores(values, lowest=21, highest=108):
    import torch
    import torchcrepe

    low, high = crepe_frequency_bounds(lowest, highest)
    # Decoders modify their input in place; retain untouched native salience.
    return torchcrepe.postprocess(
        torch.from_numpy(values.T[None]).clone(),
        fmin=low,
        fmax=high,
        decoder=torchcrepe.decode.weighted_argmax,
        return_periodicity=True,
    )


def estimate_pitch(audio, method, runtime, device="cpu", lowest=21, highest=108):
    import librosa
    import numpy as np
    import torch

    initialize()
    waveform = torch.from_numpy(audio).float().unsqueeze(0).to(device)
    with torch.inference_mode():
        if method == "rmvpe":
            source = source_directory(runtime)
            from modules.pe.rmvpe import RMVPE

            checkpoint = source / "checkpoints/rmvpe/model.pt"
            model = RMVPE(str(checkpoint), device=device)
            salience = model.mel2hidden(model.mel_extractor(waveform, center=True))
            f0 = model.decode(salience, thred=0.03)[0]
            values = salience[0].cpu().numpy()
            scores = values.max(axis=1)
            metadata = {
                "revision": REVISION,
                "checkpoint_sha256": digest(checkpoint),
                "score_kind": "salience",
                "decoder": "local_average",
                "voicing_threshold": 0.03,
            }
        elif method == "crepe":
            import torchcrepe

            batches = [
                torchcrepe.infer(frames, model="full", device=device).cpu()
                for frames in torchcrepe.preprocess(
                    waveform.cpu(), 16000, 160, batch_size=128, device=device
                )
            ]
            values = torch.cat(batches).numpy()
            f0, periodicity = decode_crepe_scores(values, lowest, highest)
            f0, scores = f0[0].numpy(), periodicity[0].numpy()
            # Periodicity is not a calibrated probability of a correct note.
            metadata = {
                "package_version": importlib.metadata.version("torchcrepe"),
                "score_kind": "periodicity",
                "decoder": "weighted_argmax",
                "voicing_threshold": None,
                "effective_frequency_range_hz": crepe_frequency_bounds(lowest, highest),
            }
        else:
            raise ValueError("unknown neural pitch method")
    pitch = librosa.hz_to_midi(np.maximum(f0, 1e-12))
    valid = (f0 > 0) & (pitch >= lowest) & (pitch <= highest)
    times = np.arange(len(f0)) * 0.01
    keep = times < len(audio) / 16000
    return {
        **metadata,
        "method": method,
        "hop_seconds": 0.01,
        "times": times[keep].tolist(),
        "pitch": [
            float(p) if v else None
            for p, v in zip(pitch[keep], valid[keep], strict=True)
        ],
        "voicing_score": scores[keep].tolist(),
        "review_status": "estimated",
    }, {"times": times[keep], "pitches": pitch_bins(), "salience": values[keep]}


class RosvotModel:
    def __init__(self, runtime, device="cpu", boundary_threshold=0.85):
        import torch
        import yaml

        initialize()
        self.source = source_directory(runtime)
        from modules.pe.rmvpe import RMVPE
        from modules.rosvot.rosvot import MidiExtractor, WordbdExtractor
        from utils.audio.mel import MelNet
        from utils.commons.ckpt_utils import load_ckpt

        checkpoint = self.source / "checkpoints"
        self.params = yaml.safe_load((checkpoint / "rosvot/config.yaml").read_text())
        self.params["note_bd_threshold"] = boundary_threshold
        self.word_params = yaml.safe_load((checkpoint / "rwbd/config.yaml").read_text())
        self.device = torch.device(device)
        self.model = MidiExtractor(self.params).eval().to(self.device)
        self.words = WordbdExtractor(self.word_params).eval().to(self.device)
        load_ckpt(self.model, str(checkpoint / "rosvot/model.pt"), verbose=False)
        load_ckpt(self.words, str(checkpoint / "rwbd/model.pt"), verbose=False)
        self.mel = MelNet(self.params)
        self.mel.to(self.device)
        self.pitch = RMVPE(str(checkpoint / "rmvpe/model.pt"), device=self.device)
        self.metadata = {
            "revision": REVISION,
            "device": device,
            "boundary_threshold": boundary_threshold,
            "note_pitch_temperature": self.params["note_pitch_temperature"],
            "note_boundary_temperature": self.params["note_bd_temperature"],
            "checkpoint_sha256": {
                name: digest(checkpoint / name / "model.pt")
                for name in ("rosvot", "rwbd", "rmvpe")
            },
        }

    def predict(self, audio, sample_rate):
        import librosa
        import numpy as np
        import torch
        from utils.audio.pitch_utils import (
            boundary2Interval,
            denorm_f0,
            f0_to_coarse,
            norm_interp_f0,
        )

        rate, hop = self.params["audio_sample_rate"], self.params["hop_size"]
        audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=rate)
        real = math.ceil(len(audio) / hop)
        length = math.ceil(real / 16) * 16
        waveform = torch.from_numpy(audio).float().unsqueeze(0).to(self.device)
        with torch.inference_mode():
            # Match upstream batch inference, including its F0 postprocessing.
            f0s, _ = self.pitch.get_pitch_batch(
                waveform,
                rate,
                hop,
                [real],
                fmin=self.params["f0_min"],
                fmax=self.params["f0_max"],
            )
            f0, uv = norm_interp_f0(f0s[0])
            f0 = (
                torch.from_numpy(np.pad(f0, (0, length - real)))
                .float()[None]
                .to(self.device)
            )
            uv = (
                torch.from_numpy(np.pad(uv, (0, length - real), constant_values=True))
                .long()[None]
                .to(self.device)
            )
            coarse = f0_to_coarse(denorm_f0(f0, uv))
            mel = self.mel(waveform)
            mel = torch.nn.functional.pad(mel, (0, 0, 0, length - mel.shape[1]))
            nonpadding = torch.arange(length, device=self.device)[None] < real
            word = self.words(
                mel=mel[:, :, : self.word_params["use_mel_bins"]],
                pitch=coarse,
                uv=uv,
                non_padding=nonpadding,
                train=False,
            )
            result = self.model(
                mel=mel[:, :, : self.params["use_mel_bins"]],
                word_bd=word["word_bd_pred"],
                pitch=coarse,
                uv=uv,
                non_padding=nonpadding,
                train=False,
            )
        boundaries = result["note_bd_pred"][0, :real].cpu().numpy()
        intervals = boundary2Interval(boundaries) * hop / rate
        count = len(intervals)
        logits = result["note_logits"][0, :count].cpu().numpy()
        softmax = torch.softmax(result["note_logits"][0, :count], dim=-1).cpu().numpy()
        return {
            "pitches": result["note_pred"][0, :count].cpu().numpy(),
            "intervals": intervals,
            "note_logits": logits,
            "note_softmax": softmax,
            "note_times": intervals.mean(axis=1),
            "note_pitch_bins": np.arange(
                self.params["note_start"], self.params["note_num"] + 1
            ),
            "note_pitch_softmax": softmax[
                :, self.params["note_start"] : self.params["note_num"] + 1
            ],
            "times": np.arange(real) * hop / rate,
            "boundary_logits": result["note_bd_logits"][0, :real].cpu().numpy(),
            "boundary_score": torch.sigmoid(result["note_bd_logits"][0, :real])
            .cpu()
            .numpy(),
            "f0": denorm_f0(f0, uv)[0, :real].cpu().numpy(),
        }


def rosvot(args):
    import numpy as np
    import soundfile as sf

    audio, rate = sf.read(args.input, dtype="float32", always_2d=True)
    if len(audio) / rate > 30:
        raise ValueError(
            "ROSVOT adapter requires <=30s excerpts; preserve source offset when cropping"
        )
    channel = int(np.argmax(np.mean(audio**2, axis=0)))
    model = RosvotModel(args.runtime, args.device)
    result = model.predict(audio[:, channel], rate)
    from utils.audio.pitch_utils import save_midi

    save_midi(result["pitches"], result["intervals"], str(args.output))
    np.savez_compressed(args.output.with_suffix(".evidence.npz"), **result)
    write_json(
        args.output.with_suffix(".candidates.json"),
        [
            {
                "id": i,
                "start_seconds": float(interval[0]),
                "end_seconds": float(interval[1]),
                "pitch": int(pitch),
                "is_rest": bool(pitch == 0),
                "top_pitches": [
                    {
                        "class_index": int(p),
                        "midi": int(p)
                        if model.params["note_start"] <= p <= model.params["note_num"]
                        else None,
                        "softmax": float(scores[p]),
                    }
                    for p in np.argsort(scores)[-3:][::-1]
                ],
                "calibrated_probability": None,
            }
            for i, (pitch, interval, scores) in enumerate(
                zip(
                    result["pitches"],
                    result["intervals"],
                    result["note_softmax"],
                    strict=True,
                )
            )
        ],
    )
    return {
        **model.metadata,
        "selected_channel": channel,
        "confidence": None,
        "evidence": "raw note/boundary logits, uncalibrated softmax/sigmoid, and F0",
    }
