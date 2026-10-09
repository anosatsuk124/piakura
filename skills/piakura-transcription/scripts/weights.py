"""Import separately obtained MuScriptor checkpoints; never transfer credentials."""

import shutil
import tempfile
from pathlib import Path

from runtime import contained, digest, write_json

CHECKPOINTS = {
    "muscriptor-small": (
        "8c127f603b807520fa465c838e9bfee8a91ada4e",
        "bbd482c786b895cf7d8f44185073d951adae2ebb8a66f82ca84cd1f84569549c",
    ),
    "muscriptor-medium": (
        "f32236969308476e01fd3aae67357de5feb05a2d",
        "ac80adbdf85d87231735fd948af7013441c0afced316c4e9067fd5d8a7fb97ec",
    ),
}


def import_weights(root, model, stream):
    revision, expected = CHECKPOINTS[model]
    target = contained(root, Path(root) / "models" / model / "model.safetensors")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=".weights-", dir=target.parent, delete=False
    ) as file:
        temporary = Path(file.name)
    try:
        with temporary.open("wb") as destination:
            shutil.copyfileobj(stream, destination)
        if digest(temporary) != expected:
            raise ValueError("checkpoint differs from pinned official weights")
        temporary.replace(target)
        write_json(
            target.with_suffix(".json"),
            {
                "revision": revision,
                "sha256": expected,
                "repository": "MuScriptor/" + model,
                "license": "CC-BY-NC-4.0 + access conditions",
            },
        )
    finally:
        temporary.unlink(missing_ok=True)
    return target
