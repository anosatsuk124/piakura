#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=skills/piakura-arranger/scripts/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
usage='Usage: export.sh [--language CODE] ARRANGEMENT-DIRECTORY DELIVERY-DIRECTORY\n'
language=
if [[ ${1:-} == --language ]]; then
  [[ $# -ge 2 ]] || {
    printf '%b' "$usage" >&2
    exit 2
  }
  language=$2
  shift 2
fi
[[ $# -eq 2 ]] || {
  printf '%b' "$usage" >&2
  exit 2
}
# The README's language: --language, else the piakura setting, which
# follows the locale (docs/i18n.md). Its words come from locales/<code>.sh.
locales="$(dirname "${BASH_SOURCE[0]}")/locales"
if [[ -z "$language" ]]; then
  language=$(arranger_tool piakura config get language 2>/dev/null | tr -d '"') || language=en
fi
[[ "$language" =~ ^[a-z]{2,3}$ && -f "$locales/$language.sh" ]] || {
  printf 'No delivery README in language %s; available:' "$language" >&2
  for available in "$locales"/*.sh; do
    printf ' %s' "$(basename "$available" .sh)" >&2
  done
  printf '\n' >&2
  exit 2
}
# shellcheck source=skills/piakura-arranger/scripts/locales/en.sh
source "$locales/$language.sh"
source_dir=$(piakura_abspath "$1")
destination=$2
[[ ! -L "$destination" ]] || {
  printf 'Distribution destination cannot be a symlink\n' >&2
  exit 2
}
destination=$(piakura_abspath "$destination")
if [[ "$destination" == "$source_dir" || "$destination" == "$source_dir/"* || "$source_dir" == "$destination/"* ]]; then
  printf 'Arrangement and distribution directories must not overlap\n' >&2
  exit 2
fi
[[ -d "$source_dir" ]] || {
  printf 'Arrangement directory does not exist: %s\n' "$source_dir" >&2
  exit 2
}
marker=.piakura-dist
if [[ -e "$destination" && (! -d "$destination" || ! -f "$destination/$marker") ]]; then
  printf 'Existing destination is not an arranger distribution: %s\n' "$destination" >&2
  exit 2
fi
parent=$(dirname "$destination")
mkdir -p -- "$parent"
staging=$(mktemp -d "$parent/.piakura-dist-XXXXXX")
backup=
cleanup() {
  local result=$?
  # Restore the previous complete delivery if replacement fails after moving it.
  if [[ -n "$backup" && ! -e "$destination" ]]; then
    piakura_rename "$backup" "$destination"
    backup=
  fi
  [[ -z "$staging" ]] || rm -rf -- "$staging"
  [[ -z "$backup" ]] || rm -rf -- "$backup"
  return "$result"
}
trap cleanup EXIT
printf 'piakura distribution v1\n' >"$staging/$marker"
msg_intro >"$staging/README.md"
scores=0
copy_group() {
  local relative=$1 label=$2 folder="$source_dir${1:+/$1}"
  local level score_path sidecar cell row="|$label|"
  for level in easy medium hard; do
    cell=—
    if [[ -e "$folder/$level.mid" || -e "$folder/$level.mml" ]]; then
      [[ -f "$folder/$level.mid" && -f "$folder/$level.mml" ]] || {
        printf 'Incomplete MIDI/MML pair: %s/%s\n' "$folder" "$level" >&2
        return 2
      }
      score_path="${relative:+$relative/}$level"
      mkdir -p -- "$staging/$(dirname "$score_path")"
      cp -- "$folder/$level.mid" "$folder/$level.mml" "$staging/$(dirname "$score_path")/"
      cell="[MIDI]($score_path.mid) · [MML]($score_path.mml)"
      for sidecar in report plan review; do
        if [[ -f "$folder/$level-$sidecar.json" ]]; then
          mkdir -p -- "$staging/${sidecar}s/$(dirname "$score_path")"
          cp -- "$folder/$level-$sidecar.json" "$staging/${sidecar}s/$score_path.json"
          cell+=" · [$(msg_link "$sidecar")](${sidecar}s/$score_path.json)"
        fi
      done
      scores=$((scores + 1))
    fi
    row+="$cell|"
  done
  printf '%s\n' "$row" >>"$staging/README.md"
}
# An explicit allowlist keeps source MIDI, obsolete scores and private musical
# studies out of the delivery. The contract is documented in ../references/distribution.md.
copy_group "" "$(msg_group standard)"
for mode in fixed-preserve fixed-auto-transpose switch-preserve switch-auto-transpose; do
  [[ -d "$source_dir/keyboard/$mode" ]] || continue
  copy_group "keyboard/$mode" "$(msg_group "$mode")"
done
[[ "$scores" -gt 0 ]] || {
  printf 'No completed easy/medium/hard MIDI/MML pairs found\n' >&2
  exit 2
}
if [[ -f "$source_dir/arrangement-report.md" ]]; then
  cp -- "$source_dir/arrangement-report.md" "$staging/report.md"
  printf '\n[%s](report.md)\n' "$(msg_report_link)" >>"$staging/README.md"
fi
msg_keyboard_guide >>"$staging/README.md"
comparison_heading=false
for excerpt in phrase harmony interlude; do
  file="comparisons/easy/$excerpt"
  [[ -f "$source_dir/$file.mid" ]] || continue
  mkdir -p -- "$staging/comparisons/easy"
  cp -- "$source_dir/$file.mid" "$staging/$file.mid"
  if [[ -f "$source_dir/$file.mml" ]]; then
    cp -- "$source_dir/$file.mml" "$staging/$file.mml"
  fi
  if [[ "$comparison_heading" == false ]]; then
    printf '\n## %s\n\n' "$(msg_comparisons)" >>"$staging/README.md"
    comparison_heading=true
  fi
  printf -- '- [%s](%s.mid)\n' "$(msg_excerpt "$excerpt")" "$file" >>"$staging/README.md"
done
msg_playing >>"$staging/README.md"
(
  cd "$staging"
  # Collect paths before opening the manifest so the checksum never includes
  # its own partially written file. Delivery file names never contain newlines.
  files=$(find . -type f ! -name SHA256SUMS | LC_ALL=C sort)
  while IFS= read -r file; do
    piakura_sha256 "$file"
  done <<<"$files" >SHA256SUMS
)
# Prepare the entire bundle before replacing an owned output directory; missing
# inputs must not leave a mixture of old and new scores in a successful delivery.
if [[ -d "$destination" ]]; then
  backup=$(mktemp -d "$parent/.piakura-dist-backup-XXXXXX")
  rmdir -- "$backup"
  piakura_rename "$destination" "$backup"
fi
piakura_rename "$staging" "$destination"
staging=
printf 'Exported %d arrangements to %s\n' "$scores" "$destination"
