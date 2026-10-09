#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=skills/piakura-arranger/scripts/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
[[ $# == 2 ]] || {
  printf 'Usage: compile.sh score.mml score.mid\n' >&2
  exit 2
}
if [[ $(piakura_abspath "$1") == "$(piakura_abspath "$2")" || "$1" -ef "$2" ]]; then
  printf 'Input and output must differ\n' >&2
  exit 2
fi
# Direct redirection would truncate an existing MIDI before an MML failure.
# Compile beside the destination and replace it only after successful output.
compiled=$(mktemp "$(dirname "$2")/.piakura-compile-XXXXXX")
trap 'rm -f -- "$compiled"' EXIT
arranger_tool sakurac-pipe <"$1" >"$compiled"
mv -f -- "$compiled" "$2"
