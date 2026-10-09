"""Audio preparation, model execution and verified handoff to piakura-arranger."""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from audio_evidence import probe
from runtime import digest, isolated_env, write_json
from setup_runtime import environment
from weights import CHECKPOINTS, import_weights
from worker import MODELS

SCRIPT = Path(__file__).resolve().parent
# The arranger skill is installed beside this one; its helpers verify handoffs.
ARRANGER_SCRIPTS = SCRIPT.parent.parent / "piakura-arranger" / "scripts"


def default_runtime():
    if os.environ.get("PIAKURA_TRANSCRIPTION_RUNTIME"):
        return Path(os.environ["PIAKURA_TRANSCRIPTION_RUNTIME"])
    cache = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(cache) / "piakura" / "transcription"


def fresh(directory):
    directory = Path(directory).absolute()
    if directory.exists() or directory.is_symlink():
        raise ValueError(
            "work directory must be new; keep previous attempts as evidence"
        )
    directory.mkdir(parents=True)
    return directory


def run(command, **kwargs):
    return subprocess.run([str(p) for p in command], check=True, **kwargs)


def setup(runtime, backend):
    env = isolated_env(runtime)
    env["PATH"] = os.environ["PATH"]
    run(
        [
            sys.executable,
            "-B",
            SCRIPT / "setup_runtime.py",
            backend,
            "--runtime",
            runtime,
        ],
        env=env,
    )


def audio_file(source, output, start=0, duration=None):
    command = ["ffmpeg", "-nostdin", "-v", "error", "-i", source, "-ss", str(start)]
    if duration is not None:
        command += ["-t", str(duration)]
    command += [
        "-map",
        "0:a:0",
        "-vn",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-c:a",
        "pcm_s16le",
        "-n",
        output,
    ]
    run(command)
    probe = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            output,
        ],
        capture_output=True,
    )
    return json.loads(probe.stdout)


def ingest(args):
    output = fresh(args.output)
    source = args.source
    env = isolated_env(args.runtime)
    env["PATH"] = os.environ["PATH"]
    if source.startswith(("https://", "http://")):
        # Keep the compressed source and metadata. Do not bypass authentication
        # or silently read browser cookies when a provider rejects the download.
        run(
            [
                "uvx",
                "--from",
                "yt-dlp==2026.8.19",
                "yt-dlp",
                "--ignore-config",
                "--no-playlist",
                "--write-info-json",
                "--no-overwrites",
                "-f",
                "bestaudio/best",
                "-o",
                str(output / "source.%(ext)s"),
                source,
            ],
            env=env,
        )
        candidates = [
            p
            for p in output.glob("source.*")
            if p.suffix not in (".json", ".part", ".ytdl")
        ]
        if len(candidates) != 1:
            raise ValueError("expected one downloaded audio/video file")
        original = candidates[0]
    else:
        original = Path(source).resolve(strict=True)
    probe = audio_file(original, output / "audio.wav", args.start, args.duration)
    write_json(
        output / "source.json",
        {
            "source": source,
            "source_sha256": digest(original),
            "audio_sha256": digest(output / "audio.wav"),
            "offset_seconds": args.start,
            "duration_requested": args.duration,
            "probe": probe,
        },
    )
    print(output / "audio.wav")


def infer(args):
    output = fresh(args.output)
    python = environment(args.runtime, args.model) / "bin/python"
    if not python.exists():
        raise ValueError("environment missing; run transcription setup first")
    env = isolated_env(args.runtime)
    env["PATH"] = os.environ["PATH"]
    command = [
        python,
        "-B",
        SCRIPT / "backend.py",
        args.model,
        args.input.resolve(),
        output / "raw.mid",
        "--runtime",
        args.runtime,
        "--device",
        args.device,
    ]
    state = {
        "model": args.model,
        "device": args.device,
        "state": "running",
        "input_sha256": digest(args.input),
    }
    write_json(output / "status.json", state)
    start = time.monotonic()
    try:
        with (output / "inference.log").open("wb") as log:
            run(command, env=env, stdout=log, stderr=log, timeout=args.timeout)
        state.update(state="succeeded", output_sha256=digest(output / "raw.mid"))
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        state["state"] = "failed"
        raise
    finally:
        state["elapsed_seconds"] = time.monotonic() - start
        write_json(output / "status.json", state)
    print(output / "raw.mid")


def handoff(args):
    output = fresh(args.output)
    score = output / "transcription.mml"
    shutil.copyfile(args.score, score)
    evidence = output / ("evidence" + args.evidence.suffix)
    shutil.copyfile(args.evidence, evidence)
    helpers = ARRANGER_SCRIPTS
    run(["bash", helpers / "compile.sh", score, output / "transcription.mid"])
    run(
        [
            "bash",
            helpers / "prepare.sh",
            output / "transcription.mid",
            output / "verified",
        ]
    )
    channels = [int(v) for v in args.melody_channels.split(",")]
    if not channels or any(c < 1 or c > 16 or c == 10 for c in channels):
        raise ValueError("melody channels must be 1..16, excluding drum channel 10")
    analysis = json.loads((output / "verified/song.json").read_text())
    found = {p["channel"] for p in analysis["parts"] if p["note_count"] > 0}
    if not set(channels).issubset(found):
        raise ValueError("selected melody channel has no notes")
    write_json(
        output / "handoff.json",
        {
            "version": 1,
            "reference_midi": "transcription.mid",
            "editable_mml": "transcription.mml",
            "melody_channels": sorted(set(channels)),
            "evidence": evidence.name,
            "quality": "provisional" if args.provisional else "reviewed",
            "sha256": {
                p.name: digest(p)
                for p in [score, output / "transcription.mid", evidence]
            },
        },
    )
    print(output / "handoff.json")


def verify_handoff(path):
    from runtime import contained

    path = Path(path).resolve()
    data = json.loads(path.read_text())
    if data.get("version") != 1 or data.get("quality") not in (
        "reviewed",
        "provisional",
    ):
        raise ValueError("unsupported handoff")
    for key in ("reference_midi", "editable_mml", "evidence"):
        relative = data[key]
        file = contained(path.parent, path.parent / relative)
        if digest(file) != data["sha256"].get(relative):
            raise ValueError(
                f"handoff artifact changed: {relative}; regenerate and revalidate"
            )
    channels = data["melody_channels"]
    if not channels or any(
        type(c) is not int or c < 1 or c > 16 or c == 10 for c in channels
    ):
        raise ValueError("invalid melody channels")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime",
        type=Path,
        default=default_runtime(),
        help="model environments and caches (default: PIAKURA_TRANSCRIPTION_RUNTIME "
        "or $XDG_CACHE_HOME/piakura/transcription)",
    )
    sub = parser.add_subparsers(dest="action", required=True)
    command = sub.add_parser("setup")
    command.add_argument(
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
    command = sub.add_parser("import-weights")
    command.add_argument("model", choices=CHECKPOINTS)
    command.add_argument("checkpoint", type=Path)
    command = sub.add_parser("ingest")
    command.add_argument("source")
    command.add_argument("output", type=Path)
    command.add_argument("--start", type=float, default=0)
    command.add_argument("--duration", type=float)
    command = sub.add_parser("infer")
    command.add_argument("input", type=Path)
    command.add_argument("output", type=Path)
    command.add_argument("--model", choices=MODELS, default="yourmt3")
    command.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    command.add_argument("--timeout", type=int, default=3600)
    command = sub.add_parser("probe")
    command.add_argument("input", type=Path)
    command.add_argument("output", type=Path)
    command.add_argument("--pitches", required=True)
    command.add_argument(
        "--windows", required=True, help="comma-separated start:end seconds"
    )
    command.add_argument("--a4", type=float, default=440)
    command = sub.add_parser(
        "review", help="beat/pitch evidence in the locked audio environment"
    )
    command.add_argument("arguments", nargs=argparse.REMAINDER)
    command = sub.add_parser("handoff")
    command.add_argument("score", type=Path)
    command.add_argument("output", type=Path)
    command.add_argument("--melody-channels", required=True)
    command.add_argument("--evidence", required=True, type=Path)
    command.add_argument("--provisional", action="store_true")
    command = sub.add_parser("verify-handoff")
    command.add_argument("manifest", type=Path)
    args = parser.parse_args()
    args.runtime = args.runtime.resolve()
    if args.action == "setup":
        setup(args.runtime, args.backend)
    elif args.action == "import-weights":
        with args.checkpoint.open("rb") as stream:
            print(import_weights(args.runtime, args.model, stream))
    elif args.action == "ingest":
        if (
            not math.isfinite(args.start)
            or args.start < 0
            or (
                args.duration is not None
                and (not math.isfinite(args.duration) or args.duration <= 0)
            )
        ):
            parser.error("start must be nonnegative and duration positive")
        ingest(args)
    elif args.action == "infer":
        if not 1 <= args.timeout <= 86400:
            parser.error("timeout must be 1..86400 seconds")
        infer(args)
    elif args.action == "probe":
        if args.output.exists() or args.output.is_symlink():
            raise ValueError("probe output directory must be new")
        result = probe(args.input, args.pitches, args.windows, args.a4)
        output = fresh(args.output)
        write_json(output / "probe.json", result)
        print(output / "probe.json")
    elif args.action == "review":
        family = "audio"
        if args.arguments and args.arguments[0] == "game":
            family = "game"
        if args.arguments and args.arguments[0] == "pitch":
            for method in ("rmvpe", "crepe"):
                if method in args.arguments or f"--method={method}" in args.arguments:
                    family = "melody"
        python = environment(args.runtime, family) / "bin/python"
        if not python.is_file():
            raise ValueError(
                f"{family} environment missing; run transcription setup {family} first"
            )
        env = isolated_env(args.runtime)
        env["TRANSCRIPTION_RUNTIME"] = str(args.runtime)
        if args.arguments and args.arguments[0] == "assist":
            env["PATH"] = os.environ["PATH"]
            if (
                "openrouter" in args.arguments
                or "--provider=openrouter" in args.arguments
            ) and "OPENROUTER_API_KEY" in os.environ:
                env["OPENROUTER_API_KEY"] = os.environ["OPENROUTER_API_KEY"]
        run([python, "-B", SCRIPT / "audio_review.py", *args.arguments], env=env)
    elif args.action == "handoff":
        handoff(args)
    else:
        print(json.dumps(verify_handoff(args.manifest), ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (
        ValueError,
        OSError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ) as error:
        print(f"transcription: {error}", file=sys.stderr)
        sys.exit(2)
