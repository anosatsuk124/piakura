#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=skills/piakura-arranger/scripts/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
[[ $# == 2 ]] || {
  printf 'Usage: prepare.sh source.mid work-directory\n' >&2
  exit 2
}
# An input already named like one of the generated files must stay untouched.
# Check every output before any conversion or compilation, including hardlinks.
for name in original-canonical.mml original.mml song.json original-canonical-roundtrip.mid original-roundtrip.mid; do
  if [[ $(piakura_abspath "$1") == "$(piakura_abspath "$2/$name")" || "$1" -ef "$2/$name" ]]; then
    printf 'Source MIDI conflicts with prepared output: %s\n' "$2/$name" >&2
    exit 2
  fi
done
mkdir -p -- "$2"
arranger_tool smf2sakura "$1" --mode canonical -o "$2/original-canonical.mml" --report "$2/song.json"
arranger_tool smf2sakura "$1" --mode pretty -o "$2/original.mml"
bash "$(dirname "${BASH_SOURCE[0]}")/compile.sh" "$2/original-canonical.mml" "$2/original-canonical-roundtrip.mid"
arranger_tool mididiff "$1" "$2/original-canonical-roundtrip.mid"
bash "$(dirname "${BASH_SOURCE[0]}")/compile.sh" "$2/original.mml" "$2/original-roundtrip.mid"
arranger_tool mididiff "$1" "$2/original-roundtrip.mid"
