#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=skills/piakura-arranger/scripts/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
[[ $# -ge 4 ]] || {
  printf 'Usage: compare.sh reference.mid arranged.mid level melody_channels [midistat options...]\n' >&2
  exit 2
}
reference=$1
score=$2
level=$3
melody=$4
shift 4
arranger_tool midistat "$score" --profile "$level" --hands RH=1,LH=2 --piano-mode solo "$@" --reference "$reference" --melody-channels "$melody" --preserve-melody --check-voicing --require-pass
