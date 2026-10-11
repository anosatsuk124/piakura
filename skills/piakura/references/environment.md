# Environment

## Platforms

| | Linux x86_64 | Linux arm64 | macOS arm64 (Apple silicon) |
|---|---|---|---|
| MIDI input, arrangement, review | yes | yes | yes |
| Transcription on this machine, directly | CPU, or CUDA with an NVIDIA GPU | no | CPU, experimental (no CUDA) |
| Transcription on an SSH worker (x86_64 Linux) | yes | yes | yes |
| Transcription in Docker | experimental | no | not recommended (no GPU in Docker Desktop) |

The Linux model environments pin x86_64 packages, and the worker image is built for x86_64; `piakura doctor` reports another architecture.

Windows is not supported; WSL2 behaves as Linux but is untested.

## What each part needs

- Always: bash, python3 3.8+, and the piakura tools (`scripts/install.sh`).
- Audio or URL input: mise (`curl https://mise.run | sh`), ffmpeg and ffprobe. mise supplies the pinned Python and uv; uv supplies yt-dlp. About 20 GB free for model environments and weights.
- SSH worker: on the worker, x86_64 Linux, key-based SSH with the host key already in `known_hosts`, Python 3.9+, mise, bubblewrap and the NVIDIA driver for CUDA. No sudo or system changes are made; everything stays in the worker directory. Check with `piakura doctor --ssh HOST --root DIR`.
- Docker worker: Docker, the NVIDIA Container Toolkit for CUDA, and while the image is private `docker login ghcr.io` with read access. Membership in the `docker` group is root-equivalent.
- Review: a browser. For FLAC/MP4 export, ffmpeg and fluidsynth on the machine running the review server; for video titles in Chinese, Japanese or Korean, fontconfig with a CJK font (for example Noto Sans CJK; Latin text needs none). MP4 encodes on the GPU when ffmpeg can there (VA-API or NVENC on Linux, VideoToolbox on macOS; `piakura doctor --review` names the encoder and, without one, what this GPU needs), otherwise on the CPU.

`piakura doctor` reports what is missing with an install command for this system.

## Where things go

| What | Where |
|---|---|
| Tools | `${XDG_DATA_HOME:-~/.local/share}/piakura/releases/<version>/bin` (`current` links the latest) |
| `piakura` on the PATH, if chosen | `${XDG_BIN_HOME:-~/.local/bin}/piakura`, a link to `current/bin/piakura` |
| Settings | `${XDG_CONFIG_HOME:-~/.config}/piakura/config.json`, `.piakura/config.json` |
| Transcription environments, weights, caches | `${XDG_CACHE_HOME:-~/.cache}/piakura/transcription` (several GB) |
| SSH worker records | `${XDG_STATE_HOME:-~/.local/state}/piakura/workers/` |
| Review UI preferences | the review tool's own settings directory (`piakura-review`) |
| Work and deliveries | `piakura/work/<slug>`, `piakura/dist/<slug>` unless chosen otherwise |

## Removing piakura

Remove the skills with the tool that installed them (`npx skills remove …`), remove the PATH link with `bash scripts/install.sh --unlink-bin` (it leaves anything piakura did not make), then delete the directories above that you no longer need. On an SSH worker, delete the worker directory (only one carrying the `.piakura-worker` marker).
