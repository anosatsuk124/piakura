"""Experimental pinned guitar separation on an unchanged 44.1-kHz sample clock."""

import argparse
import importlib.metadata
import resource
import sys
import time
from functools import partial
from pathlib import Path
from unittest.mock import patch

from runtime import digest, write_json
from setup_runtime import download

REVISION = "6409e7f88754b07ef7ca3bd1b76a15f010f1672a"
MODEL_REPO = "becruily/mel-band-roformer-guitar"
FILES = {
    "becruily_guitar.ckpt": "83472bbf125774af5282d2e0b86df89eaf2dd45e8a4ec8d68e820ebf3e42a83c",
    "config_guitar_becruily.yaml": "b681c3f886251b04b666b3f06e87ce65d7ec610e40b5d75915c01782e5444b0e",
}


def separate(source, output, model_directory, source_offset=0, threads=4):
    import numpy as np
    import soundfile as sf
    import torch
    from audio_separator.separator import Separator
    from audio_separator.separator.uvr_lib_v5.roformer import mel_band_roformer

    if importlib.metadata.version("audio-separator") != "0.47.0":
        raise ValueError("use the pinned guitar environment; adapter requires 0.47.0")
    source, output = Path(source).resolve(), Path(output).resolve()
    model_directory = Path(model_directory).resolve()
    info = sf.info(source)
    if (info.samplerate, info.channels) != (44100, 2) or info.frames < 441000:
        raise ValueError("supply at least 10 seconds of 44.1-kHz stereo audio")
    if source_offset < 0 or not np.isfinite(source_offset) or not 1 <= threads <= 32:
        raise ValueError("invalid source offset or CPU thread count")
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "state": "running",
        "source": str(source),
        "source_sha256": digest(source),
        "source_offset_seconds": source_offset,
        "sample_rate": info.samplerate,
        "frames": info.frames,
        "model_repo": MODEL_REPO,
        "revision": REVISION,
        "model_files_sha256": FILES,
        "script_sha256": digest(__file__),
        "environment_lock_sha256": digest(
            Path(__file__).parent / "environments/guitar.lock"
        ),
        "audio_separator_version": importlib.metadata.version("audio-separator"),
        "torch_version": torch.__version__,
        "device": "cpu",
        "precision": "float32",
        "window_samples": 485100,
        "overlap_count": 2,
        "pitch_shift": 0,
        "architecture_workaround": "forward mlp_expansion_factor=1 to MaskEstimator",
        "permission_source": f"https://huggingface.co/{MODEL_REPO}/discussions/9",
        "output": [],
    }
    started = time.monotonic()
    write_json(output / "separation.json", manifest)
    try:
        for name, expected in FILES.items():
            download(
                f"https://huggingface.co/{MODEL_REPO}/resolve/{REVISION}/{name}",
                model_directory / name,
                expected,
            )
        torch.set_num_threads(threads)
        torch.set_num_interop_threads(1)
        torch.manual_seed(0)

        class LocalGuitar(Separator):
            def download_model_files(self, filename):
                if filename != "becruily_guitar.ckpt":
                    raise ValueError("unexpected checkpoint")
                return (
                    filename,
                    "MDXC",
                    "becruily guitar",
                    str(model_directory / filename),
                    str(model_directory / "config_guitar_becruily.yaml"),
                )

        # FLOAT input avoids another PCM quantization during stem export. This
        # preserves sample positions; it does not resample, trim or align.
        samples, rate = sf.read(source, dtype="float32", always_2d=True)
        if not np.isfinite(samples).all():
            raise ValueError("non-finite input samples")
        master = output / "input.wav"
        sf.write(master, samples, rate, subtype="FLOAT")
        separator = LocalGuitar(
            model_file_dir=str(model_directory),
            output_dir=str(output),
            output_format="WAV",
            use_soundfile=True,
            sample_rate=44100,
            normalization_threshold=1.0,
            amplification_threshold=0.0,
            use_autocast=False,
            use_native_fp16=False,
            use_torch_compile=False,
            mdxc_params={
                "segment_size": 1101,
                "override_model_segment_size": False,
                "batch_size": 1,
                "overlap": 2,
                "pitch_shift": 0,
            },
        )
        separator.torch_device = torch.device("cpu")
        # Version 0.47.0 stores the factor but fails to forward it when building
        # masks. Fix construction only; retain strict checkpoint loading and
        # leave the installed library/weights unchanged. See separation ref.
        with patch.object(
            mel_band_roformer,
            "MaskEstimator",
            partial(mel_band_roformer.MaskEstimator, mlp_expansion_factor=1),
        ):
            separator.load_model("becruily_guitar.ckpt")
        for name in separator.separate(str(master)):
            path = output / name
            result, rate = sf.read(path, always_2d=True)
            if result.shape != samples.shape or rate != 44100:
                raise ValueError("output changed sample count, rate or channels")
            if not np.isfinite(result).all():
                raise ValueError("non-finite model output")
            manifest["output"].append(
                {
                    "file": path.name,
                    "sha256": digest(path),
                    "frames": len(result),
                    "subtype": sf.info(path).subtype,
                    "rms": float(np.sqrt(np.mean(result * result))),
                }
            )
        if len(manifest["output"]) != 2:
            raise ValueError("expected Guitar and Other outputs")
        manifest["state"] = "completed"
    except Exception as error:
        manifest.update(state="failed", error=str(error))
        raise
    finally:
        manifest["elapsed_seconds"] = time.monotonic() - started
        manifest["peak_rss_kib_linux"] = resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss
        write_json(output / "separation.json", manifest)
    return output / "separation.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path, help="new ignored evidence directory")
    parser.add_argument("--model-directory", required=True, type=Path)
    parser.add_argument("--source-offset", type=float, default=0)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    print(
        separate(
            args.source,
            args.output,
            args.model_directory,
            args.source_offset,
            args.threads,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        print(f"guitar-separation: {error}", file=sys.stderr)
        sys.exit(2)
