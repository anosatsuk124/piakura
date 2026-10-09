"""Adapters call upstream inference; musical corrections belong in SakuraMML."""

import argparse
import importlib.metadata
import json
import os
import resource
import shutil
import sys
import time
from contextlib import nullcontext
from pathlib import Path

from runtime import digest, write_json

YOURMT3_REVISION = "5e66c1ea173a8186e0d20432b841d3180cc015b5"
YOURMT3_EXPERIMENT = (
    "mc13_256_g4_all_v7_mt3f_sqr_rms_moe_wf4_n8k2_silu_rope_rp_b36_nops"
)
YOURMT3_CHECKPOINT = f"amt/logs/2024/{YOURMT3_EXPERIMENT}/checkpoints/last.ckpt"
YOURMT3_SHA256 = "ae38e415c79efd5592dcb9b658cdb99ddb11d4c4e1eaa364cab04a052473fc25"


def yourmt3(args):
    import torch

    source = Path(args.runtime) / "models/yourmt3" / YOURMT3_REVISION
    sys.path[:0] = [str(source), str(source / "amt/src")]
    from config.config import shared_cfg

    shared_cfg["WANDB"]["save_dir"] = str(source / "amt/logs")
    from model_helper import load_model_checkpoint, transcribe

    # Upstream's web helper assumes CUDA and batch=8. Keep its decoding and MIDI
    # writer, but force one batch for shared 8GB GPUs and CPU parity.
    flags = [
        YOURMT3_EXPERIMENT + "@last.ckpt",
        "-p",
        "2024",
        "-tk",
        "mc13_full_plus_256",
        "-dec",
        "multi-t5",
        "-nl",
        "26",
        "-enc",
        "perceiver-tf",
        "-sqr",
        "1",
        "-ff",
        "moe",
        "-wf",
        "4",
        "-nmoe",
        "8",
        "-kmoe",
        "2",
        "-act",
        "silu",
        "-epe",
        "rope",
        "-rp",
        "1",
        "-ac",
        "spec",
        "-hop",
        "300",
        "-atc",
        "1",
        "-pr",
        "32",
        "-wb",
        "disabled",
    ]
    checkpoint = source / YOURMT3_CHECKPOINT
    if digest(checkpoint) != YOURMT3_SHA256:
        raise ValueError("YourMT3 checkpoint hash mismatch")
    model = load_model_checkpoint(flags, device="cpu").to(args.device)
    inference = model.inference_file

    def single_batch(*values, **keywords):
        keywords["bsz"] = 1
        return inference(*values, **keywords)

    model.inference_file = single_batch
    context = (
        torch.autocast("cuda", dtype=torch.float16)
        if args.device == "cuda"
        else nullcontext()
    )
    with torch.inference_mode(), context:
        result = transcribe(model, {"filepath": str(args.input), "track_name": "raw"})
    shutil.copyfile(result, args.output)
    return {
        "revision": YOURMT3_REVISION,
        "checkpoint_sha256": YOURMT3_SHA256,
        "model": "YPTF.MoE+Multi noPS",
        "confidence": None,
    }


def muscriptor(args):
    from muscriptor.transcription_model import TranscriptionModel

    # An explicit local checkpoint avoids mutable aliases and remote auth state.
    checkpoint = Path(args.runtime) / "models" / args.model / "model.safetensors"
    if not checkpoint.is_file():
        raise ValueError(
            f"missing licensed checkpoint: {checkpoint}; import-weights first"
        )
    manifest = json.loads(checkpoint.with_suffix(".json").read_text())
    if digest(checkpoint) != manifest["sha256"]:
        raise ValueError("MuScriptor checkpoint hash mismatch")
    model = TranscriptionModel.load_model(
        weights_path=checkpoint,
        device=args.device,
        dtype="float16" if args.device == "cuda" else "float32",
    )
    # MuScriptor 0.3 defaults to beat detection that can shift onsets. Keep raw
    # timing here; the skill reviews beat estimates before rhythmic corrections.
    args.output.write_bytes(
        model.transcribe_to_midi(str(args.input), batch_size=1, detect_tempo=False)
    )
    return {
        **manifest,
        "model": args.model,
        "confidence": None,
        "tempo_detection": False,
    }


def basic_pitch(args):
    import numpy as np
    from basic_pitch import FilenameSuffix, build_icassp_2022_model_path
    from basic_pitch.constants import FREQ_BINS_CONTOURS, FREQ_BINS_NOTES
    from basic_pitch.inference import predict
    from basic_pitch.note_creation import model_frames_to_time

    # Use ONNX explicitly; installing TensorFlow does not select the runtime.
    model = build_icassp_2022_model_path(FilenameSuffix.onnx)
    outputs, midi, events = predict(str(args.input), model_or_model_path=model)
    midi.write(str(args.output))
    np.savez_compressed(args.output.with_suffix(".activations.npz"), **outputs)
    # The upstream clock includes a per-window correction. A naive hop/rate
    # axis drifts and would mislead onset review on a full recording.
    np.savez_compressed(
        args.output.with_suffix(".evidence.npz"),
        times=model_frames_to_time(len(outputs["note"])),
        pitches=69 + 12 * np.log2(FREQ_BINS_NOTES / 440),
        contour_pitches=69 + 12 * np.log2(FREQ_BINS_CONTOURS / 440),
        **outputs,
    )
    # Upstream note tuples contain numpy scalar values; JSON uses native types.
    native = json.loads(json.dumps(events, default=lambda value: value.tolist()))
    write_json(args.output.with_suffix(".events.json"), native)
    return {
        "version": importlib.metadata.version("basic-pitch"),
        "model": "ICASSP_2022 ONNX",
        "confidence": None,
        "evidence": "uncalibrated frame/onset/contour activations",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "model",
        choices=[
            "yourmt3",
            "muscriptor-small",
            "muscriptor-medium",
            "basic-pitch",
            "rosvot",
            "sheetsage2",
        ],
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    args.input, args.output = args.input.resolve(), args.output.resolve()
    if args.input == args.output or args.output.exists():
        parser.error("output must be a new file distinct from input")
    if args.device == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["OMP_NUM_THREADS"] = "4"
    started = time.monotonic()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    os.chdir(args.output.parent)
    from melody_backend import rosvot
    from sheetsage2_backend import sheetsage2

    metadata = (
        sheetsage2(args)
        if args.model == "sheetsage2"
        else rosvot(args)
        if args.model == "rosvot"
        else yourmt3(args)
        if args.model == "yourmt3"
        else basic_pitch(args)
        if args.model == "basic-pitch"
        else muscriptor(args)
    )
    if not args.output.is_file() or args.output.read_bytes()[:4] != b"MThd":
        raise ValueError("inference did not produce an SMF")
    metadata.update(
        input_sha256=digest(args.input),
        output_sha256=digest(args.output),
        elapsed_seconds=time.monotonic() - started,
        max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        device=args.device,
    )
    if "torch" in sys.modules and args.device == "cuda":
        import torch

        metadata["peak_cuda_allocated_bytes"] = torch.cuda.max_memory_allocated()
    write_json(args.output.with_suffix(".run.json"), metadata)


if __name__ == "__main__":
    main()
