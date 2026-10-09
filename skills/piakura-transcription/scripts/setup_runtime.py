"""Install pinned inference environments inside an explicit runtime directory."""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

from backend import YOURMT3_CHECKPOINT, YOURMT3_REVISION, YOURMT3_SHA256
from game_backend import ARCHIVE_SHA256 as GAME_SHA256
from game_backend import VERSION as GAME_VERSION
from runtime import contained, digest, write_json

SCRIPT = Path(__file__).resolve().parent
ROSVOT_REVISION = "3c8332bf43adae35f6e4d64971862f2f6139b310"


def fetch_game(root):
    base = Path(root) / "models/game" / GAME_VERSION
    name = f"GAME-{GAME_VERSION}-large-onnx"
    archive_path = base / f"{name}.zip"
    download(
        f"https://github.com/openvpi/GAME/releases/download/v{GAME_VERSION}/{name}.zip",
        archive_path,
        GAME_SHA256,
    )
    with zipfile.ZipFile(archive_path) as archive:
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            path = contained(base, base / entry.filename)
            path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(entry) as src, path.open("wb") as dst:
                shutil.copyfileobj(src, dst)
    source = base / name
    write_json(
        base / "source.json",
        {
            "archive_sha256": GAME_SHA256,
            "license": "CC-BY-NC-SA-4.0",
            "files": {p.name: digest(p) for p in source.iterdir() if p.is_file()},
        },
    )


def fetch_rosvot(root):
    base = Path(root) / "models/rosvot"
    source = base / ROSVOT_REVISION
    download(
        f"https://codeload.github.com/RickyL-2000/ROSVOT/tar.gz/{ROSVOT_REVISION}",
        base / "source.tar.gz",
        "e24c41b5918ffe5443e6058091b23bd5146bb7a4fb610d2153beb7db107983ad",
    )
    download(
        "https://drive.usercontent.google.com/download?id=1JNtNT37KiLq9uFQqHk7JFs-3trxd3bRh&export=download&confirm=t",
        base / "checkpoints.zip",
        "b6055e81315b93415c9bd7fc48e10a28a3da1bea960cab7385483bd7443ba852",
    )
    with tarfile.open(base / "source.tar.gz") as archive:
        for entry in archive:
            if not entry.isfile():
                continue
            path = contained(source, source / Path(*Path(entry.name).parts[1:]))
            path.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(entry) as src, path.open("wb") as dst:
                shutil.copyfileobj(src, dst)
    with zipfile.ZipFile(base / "checkpoints.zip") as archive:
        for entry in archive.infolist():
            if entry.is_dir() or not entry.filename.startswith("checkpoints/"):
                continue
            path = contained(source, source / entry.filename)
            path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(entry) as src, path.open("wb") as dst:
                shutil.copyfileobj(src, dst)
    write_json(
        source / "source.json",
        {
            "revision": ROSVOT_REVISION,
            "files": {
                str(p.relative_to(source)): digest(p)
                for p in sorted(source.rglob("*"))
                if p.is_file() and p.name != "source.json"
            },
        },
    )


def download(url, path, expected=None):
    path = Path(path)
    if path.is_file() and (expected is None or digest(path) == expected):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".download")
    try:
        with (
            urllib.request.urlopen(url, timeout=60) as response,
            temporary.open("wb") as stream,
        ):
            shutil.copyfileobj(response, stream)
        if expected and digest(temporary) != expected:
            raise ValueError(f"checksum mismatch: {path.name}")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def fetch_yourmt3(root):
    target = Path(root) / "models/yourmt3" / YOURMT3_REVISION
    api = f"https://huggingface.co/api/spaces/mimbres/YourMT3/tree/{YOURMT3_REVISION}/amt/src?recursive=true&limit=1000"
    entries = json.load(urllib.request.urlopen(api, timeout=30))
    paths = [
        e["path"] for e in entries if e["type"] == "file" and e["path"].endswith(".py")
    ]
    paths += ["model_helper.py", "README.md", YOURMT3_CHECKPOINT]
    for relative in paths:
        path = contained(target, target / relative)
        expected = YOURMT3_SHA256 if relative == YOURMT3_CHECKPOINT else None
        download(
            f"https://huggingface.co/spaces/mimbres/YourMT3/resolve/{YOURMT3_REVISION}/{relative}",
            path,
            expected,
        )
    write_json(
        target / "source.json",
        {"revision": YOURMT3_REVISION, "files": {p: digest(target / p) for p in paths}},
    )


def family_for(backend):
    if backend == "rosvot":
        return "melody"
    return "muscriptor" if backend.startswith("muscriptor") else backend


def lock_for(family):
    # The Linux locks pin CUDA wheels. macOS on Apple silicon (CPU only, an
    # experimental path) has separate locks for the families that resolve
    # there; the others are not available on macOS.
    if sys.platform == "darwin":
        lock = SCRIPT / "environments" / (family + ".darwin-arm64.lock")
        if platform.machine() != "arm64" or not lock.exists():
            raise ValueError(
                f"{family} is not available on this Mac; use an SSH worker"
            )
        return lock
    return SCRIPT / "environments" / (family + ".lock")


def environment(root, backend):
    # The directory is keyed by the whole lock file, header comments included,
    # so the locks keep the pre-rename `skills/music-transcription` paths in
    # their headers: editing them would rebuild every multi-GB environment.
    # Regenerate them with the new path only when dependencies change.
    family = family_for(backend)
    name = family + "-" + digest(lock_for(family))[:12]
    if os.environ.get("PIAKURA_CONTAINER") == "1":
        # A venv links the image's interpreter; a new Python needs a new env.
        name += "-py" + ".".join(map(str, sys.version_info[:3]))
    return Path(root) / "envs" / name


def setup(root, backend):
    root = Path(root).resolve()
    family = family_for(backend)
    lock = lock_for(family)
    env = contained(root, environment(root, backend))
    # mise and uv state directories are supplied by isolated_env in the caller.
    # The worker image has no mise: it ships the pinned uv and Python itself.
    uv = os.environ.get("PIAKURA_UV")
    mise = os.environ.get("PIAKURA_MISE") or shutil.which("mise")
    if not uv and not mise:
        raise ValueError("mise is required")
    venv = (
        [uv, "venv", "--python", sys.executable]
        if uv
        else [
            mise,
            "exec",
            "uv@0.12.23",
            "python@3.11.17",
            "--",
            "uv",
            "venv",
            "--python",
            "3.11.17",
        ]
    )
    pip = [uv] if uv else [mise, "exec", "uv@0.12.23", "--", "uv"]
    if not (env / ".ready.json").exists():
        indexes = (
            [
                "--index-url",
                "https://download.pytorch.org/whl/cu126",
                "--extra-index-url",
                "https://pypi.org/simple",
                "--index-strategy",
                "unsafe-best-match",
            ]
            if family == "sheetsage2"
            else []
        )
        # This lock pins CUDA 12.6. PyPI supplies NVIDIA/Triton wheels: the
        # corresponding mirror routes timed out or had different archive bytes.
        subprocess.run([*venv, str(env)], check=True)
        subprocess.run(
            [
                *pip,
                "pip",
                "sync",
                "--python",
                str(env / "bin/python"),
                "--require-hashes",
                str(lock),
                *indexes,
            ],
            check=True,
        )
        write_json(env / ".ready.json", {"lock_sha256": digest(lock)})
    if backend == "yourmt3":
        fetch_yourmt3(root)
    elif family == "melody":
        fetch_rosvot(root)
    elif family == "game":
        fetch_game(root)
    print(json.dumps({"environment": str(env), "backend": backend}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "backend",
        choices=[
            "yourmt3",
            "muscriptor",
            "basic-pitch",
            "demucs",
            "guitar",
            "audio",
            "melody",
            "game",
            "sheetsage2",
        ],
    )
    parser.add_argument("--runtime", required=True, type=Path)
    args = parser.parse_args()
    setup(args.runtime, args.backend)
