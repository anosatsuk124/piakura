#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=skills/piakura-arranger/scripts/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
[[ $# -ge 2 ]] || {
  printf 'Usage: readable-reference.sh reference.mid work-directory [smf2sakura readable options...]\n' >&2
  exit 2
}
reference=$1
work=$2
shift 2
for name in reference.readable.mml reference.readable.json reference.readable.mid; do
  if [[ $(piakura_abspath "$reference") == "$(piakura_abspath "$work/$name")" || "$reference" -ef "$work/$name" ]]; then
    printf 'Reference conflicts with readable output: %s\n' "$work/$name" >&2
    exit 2
  fi
done
mkdir -p -- "$work"
# The readable reference is the quantized melody contract arrangements are
# written against; its report records how far it moved from the reference.
arranger_tool smf2sakura "$reference" --mode readable "$@" \
  -o "$work/reference.readable.mml" --readable-report "$work/reference.readable.json"
bash "$(dirname "${BASH_SOURCE[0]}")/compile.sh" "$work/reference.readable.mml" "$work/reference.readable.mid"
python3 - "$work/reference.readable.json" <<'PY'
import json
import sys

r = json.load(open(sys.argv[1]))
n, o = r["notes"], r["onset_ms"]
print(
    f"readable reference: bars {r['first_bar']}-{r['last_bar']}, offset {r['offset_seconds']} s, "
    f"notes {n['input']}->{n['output']} (merged {n['merged'] + n['unison']}, ornaments {n['ornaments']}), "
    f"onset p95 {o['p95']} ms max {o['max']} ms, end p95 {r['end_ms']['p95']} ms"
)
for w in r["warnings"]:
    print("warning:", w)
PY
