#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=skills/piakura-arranger/scripts/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
[[ $# -ge 3 ]] || {
  printf 'Usage: validate.sh score.mid level report.json [reference.mid melody_channels [hands]] [midistat options...]\n' >&2
  exit 2
}
score=$1
level=$2
report=$3
shift 3
reference_args=()
hands=RH=1,LH=2
if [[ $# -gt 0 && $1 != --* ]]; then
  [[ $# -ge 2 && $2 != --* ]] || {
    printf 'Reference requires melody channels\n' >&2
    exit 2
  }
  reference_args=(--reference "$1" --melody-channels "$2")
  shift 2
  if [[ $# -gt 0 && $1 != --* ]]; then
    hands=$1
    shift
  fi
fi
preservation_args=()
if [[ ${#reference_args[@]} -gt 0 ]]; then
  preservation_args=(--preserve-melody)
fi
# The trailing midistat-options form must enforce the same reference contract.
for option in "$@"; do
  case "$option" in
  --reference | --reference=*) preservation_args=(--preserve-melody) ;;
  esac
done
# Completion invariants follow optional flags so trailing '=false' cannot
# turn a failed score into a delivery. The report always describes this MIDI.
arranger_tool midistat "$score" --profile "$level" --hands "$hands" --piano-mode solo ${reference_args[@]+"${reference_args[@]}"} "$@" ${preservation_args[@]+"${preservation_args[@]}"} --check-voicing --require-pass --json -o "$report"
