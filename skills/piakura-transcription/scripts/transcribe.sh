#!/usr/bin/env bash
set -euo pipefail
# Run transcribe.py with the pinned Python and uv; uvx (yt-dlp, Hugging Face CLI)
# comes from the same uv. Arguments and relative paths pass through unchanged.
here=$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
exec mise exec python@3.11.17 uv@0.12.23 -- python -B "$here/transcribe.py" "$@"
