"""Small stdlib helpers shared by local and remote transcription commands."""

import hashlib
import json
import os
import tempfile
from pathlib import Path


def digest(path):
    # Not hashlib.file_digest (3.11+): worker hosts run this with their own
    # python3, which may be as old as 3.9.
    sha = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            sha.update(block)
    return sha.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def contained(root, path):
    root, path = Path(root).resolve(), Path(path)
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"path escapes working directory: {path}")
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError(f"symlink path refused: {part}")
    return path


def isolated_env(root):
    """Redirect every tool's persistent state without changing HOME."""
    root = Path(root).resolve()
    env = {
        k: os.environ[k]
        for k in ("HOME", "USER", "LANG", "SSL_CERT_FILE")
        if k in os.environ
    }
    env["PATH"] = "/usr/local/bin:/usr/bin:/bin"
    locations = {
        "XDG_CACHE_HOME": "cache/xdg",
        "XDG_CONFIG_HOME": "config/xdg",
        "XDG_DATA_HOME": "data/xdg",
        "XDG_STATE_HOME": "state/xdg",
        "MISE_DATA_DIR": "tools/mise",
        "MISE_CACHE_DIR": "cache/mise",
        "MISE_STATE_DIR": "state/mise",
        "MISE_CONFIG_DIR": "config/mise",
        "MISE_TMP_DIR": "tmp",
        "UV_CACHE_DIR": "cache/uv",
        "UV_PYTHON_INSTALL_DIR": "tools/python",
        "UV_PYTHON_BIN_DIR": "tools/bin",
        "HF_HOME": "cache/huggingface",
        "HF_HUB_CACHE": "cache/huggingface/hub",
        "TORCH_HOME": "cache/torch",
        "CUDA_CACHE_PATH": "cache/cuda",
        "TRITON_CACHE_DIR": "cache/triton",
        "NUMBA_CACHE_DIR": "cache/numba",
        "TMPDIR": "tmp",
        "MPLCONFIGDIR": "cache/matplotlib",
        "WANDB_DIR": "cache/wandb",
        "WANDB_CACHE_DIR": "cache/wandb-cache",
    }
    for key, relative in locations.items():
        path = contained(root, root / relative)
        path.mkdir(parents=True, exist_ok=True)
        env[key] = str(path)
    env.update(
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONNOUSERSITE="1",
        WANDB_MODE="disabled",
        HF_HUB_DISABLE_TELEMETRY="1",
        DO_NOT_TRACK="1",
        MISE_YES="1",
    )
    env["MISE_TRUSTED_CONFIG_PATHS"] = str(root)
    return env
