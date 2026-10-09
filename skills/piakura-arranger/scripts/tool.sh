#!/usr/bin/env bash
set -euo pipefail
# Run one piakura tool, e.g. `bash tool.sh smf2sakura score.mid --mode readable`.
# shellcheck source=skills/piakura-arranger/scripts/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
[[ $# -ge 1 ]] || {
  printf 'Usage: tool.sh TOOL [ARGS...]\n' >&2
  exit 2
}
arranger_tool "$@"
