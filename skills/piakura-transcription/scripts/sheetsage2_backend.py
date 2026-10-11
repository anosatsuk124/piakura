"""Pinned upstream lead-sheet inference; raw notes require musical review.

Native `scores` are grammar-masked token logits, not probabilities. Keep them
and the unmasked logits, then expose a small explicitly conditional summary.
"""

import json
import os
import shutil

from runtime import digest, write_json

REVISION = "32c7c7473e7b59e1ed36bd8a8fefbd11ae8d468a"
CHECKPOINT_SHA256 = "b235f68091a5f5b644000f2b5acb57d1e70432aca2b34ab1b9cf27236e1f4274"
BASE_REVISION = "d8ba1c745e733b3908ce6ad16ebeb17ac7600a42"
BASE_SHA256 = "e6dd2ab187d6dd62b6521cd7d8f932e237acf0c5757745a7232082e28391350d"


def token_evidence(directory, tokenizer):
    import torch
    from safetensors.torch import load_file

    windows = json.loads((directory / "tokens.json").read_text())
    rows = []
    for window in windows:
        index = window["window_index"]
        folder = directory / "tensors" / f"window-{index:04d}"
        for path in sorted(folder.glob("tokens-*.safetensors")):
            tensors = load_file(path)
            positions, scores = tensors["token_position"], tensors["scores"]
            if scores.ndim != 2 or len(positions) != len(scores):
                raise ValueError("unexpected token evidence axes")
            probabilities = torch.softmax(scores.float(), dim=-1)
            if not torch.isfinite(probabilities).all():
                raise ValueError("invalid masked token distribution")
            values, indices = probabilities.topk(5, dim=-1)
            for i, position in enumerate(positions.tolist()):
                if not 0 <= position < len(window["tokens"]):
                    raise ValueError("token position outside generated window")
                chosen = window["tokens"][position]
                rows.append(
                    {
                        "window_index": index,
                        "window_start_seconds": window["start"],
                        "token_position": position,
                        "chosen_token": chosen,
                        "chosen_label": tokenizer.describe(chosen),
                        "conditional_probability": float(probabilities[i, chosen]),
                        "alternatives": [
                            {
                                "token": token,
                                "label": tokenizer.describe(token),
                                "conditional_probability": probability,
                            }
                            for token, probability in zip(
                                indices[i].tolist(), values[i].tolist(), strict=True
                            )
                            if probability > 0
                        ],
                        "calibrated_probability": None,
                    }
                )
    return {
        "score_semantics": "softmax of grammar-masked logits, conditional on the generated prefix; not note correctness",
        "timebase": "window origins in input-file seconds; token positions are not audio frames",
        "raw_tensors": "tensors/window-*/tokens-*.safetensors",
        "rows": rows,
    }


def sheetsage2(args):
    # Public revision only: no host credentials are needed or forwarded.
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    import torch
    from huggingface_hub import hf_hub_download
    from transformers import AutoModel

    torch.set_num_threads(4)
    torch.manual_seed(47)
    checkpoint = hf_hub_download(
        "m-a-p/SheetSage2", "model.safetensors", revision=REVISION, token=False
    )
    if digest(checkpoint) != CHECKPOINT_SHA256:
        raise ValueError("SheetSage2 checkpoint hash mismatch")
    model = (
        AutoModel.from_pretrained(
            "m-a-p/SheetSage2",
            revision=REVISION,
            code_revision=REVISION,
            trust_remote_code=True,
            token=False,
        )
        .eval()
        .to(args.device)
    )
    if (model.config.base_model_revision, model.config.base_model_sha256) != (
        BASE_REVISION,
        BASE_SHA256,
    ):
        raise ValueError("unexpected SheetSage2 base model")
    # Upstream also verifies its pinned base-model weights and code. Older GPUs
    # lack native BF16; FP32 is explicit on both CPU and GPU for parity.
    directory = args.output.parent / "sheetsage2"
    if directory.exists():
        raise ValueError("SheetSage2 output directory must be new")
    result = model.transcribe(
        args.input,
        output_dir=directory,
        dtype="fp32",
        export_logits=True,
        export_scores=True,
        progress=lambda value: print(json.dumps(value), flush=True),
    )
    shutil.copyfile(directory / "transcription.mid", args.output)
    write_json(
        directory / "token-evidence.json", token_evidence(directory, model.tokenizer)
    )
    return {
        "model": "SheetSage2",
        "revision": REVISION,
        "checkpoint_sha256": CHECKPOINT_SHA256,
        "base_revision": BASE_REVISION,
        "base_sha256": BASE_SHA256,
        "dtype": "fp32",
        "seed": 47,
        "license": "CC-BY-NC-4.0",
        "confidence": None,
        "duration_seconds": result["duration_seconds"],
        "review_status": "raw lead-sheet proposals; check octaves, voices, attacks, releases and harmony",
        "evidence": "sheetsage2/token-evidence.json and native tensors; uncalibrated",
        "warnings": result["warnings"],
        # Upstream can return usable timed MIDI with a failed ABC export. Keep
        # that partial failure visible even when its warnings array is empty.
        "notation_error": result.get("abc_error"),
        "notation_diagnostics": result.get("diagnostics", []),
    }
