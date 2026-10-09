#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=skills/piakura-arranger/scripts/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
[[ $# -eq 2 ]] || {
  printf 'Usage: export.sh ARRANGEMENT-DIRECTORY DELIVERY-DIRECTORY\n' >&2
  exit 2
}
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
cat >"$staging/README.md" <<'GUIDE'
# ピアノ演奏用MIDI

MIDIを開いて演奏・再生できます。編集用のSakuraMMLはMIDIの隣にあります。
通常版から始め、小型鍵盤では鍵盤モードに合う25鍵版を選んでください。
音域・移調・切替位置・検証結果は各ファイルのレポートと編曲計画で確認できます。

|版|Easy|Medium|Hard|
|---|---|---|---|
GUIDE
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
          case "$sidecar" in
          report) cell+=" · [検証](reports/$score_path.json)" ;;
          plan) cell+=" · [計画](plans/$score_path.json)" ;;
          review) cell+=" · [配置の例外](reviews/$score_path.json)" ;;
          esac
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
copy_group "" "通常版"
for mode in fixed-preserve fixed-auto-transpose switch-preserve switch-auto-transpose; do
  [[ -d "$source_dir/keyboard/$mode" ]] || continue
  # These backticks are literal Markdown code spans in the generated README.
  # shellcheck disable=SC2016
  case "$mode" in
  fixed-preserve) label='25鍵・固定・原調（`fixed-preserve`）' ;;
  fixed-auto-transpose) label='25鍵・固定・移調（`fixed-auto-transpose`）' ;;
  switch-preserve) label='25鍵・切替・原調（`switch-preserve`）' ;;
  switch-auto-transpose) label='25鍵・切替・移調（`switch-auto-transpose`）' ;;
  esac
  copy_group "keyboard/$mode" "$label"
done
[[ "$scores" -gt 0 ]] || {
  printf 'No completed easy/medium/hard MIDI/MML pairs found\n' >&2
  exit 2
}
if [[ -f "$source_dir/arrangement-report.md" ]]; then
  cp -- "$source_dir/arrangement-report.md" "$staging/report.md"
  printf '\n[編曲結果・演奏条件・切替表](report.md)\n' >>"$staging/README.md"
fi
cat >>"$staging/README.md" <<'GUIDE'

## keyboard/の名前と選び方

フォルダ名は `<range-mode>-<key-policy>` です。

- `fixed`: 曲全体で同じ25鍵を使い、曲中のOCT切替を行いません。演奏前には目標音域へ設定します。
- `switch`: 区間ごとに実機のOCT設定を変更します。最低2秒の操作用休符があり、レポートの切替表に従って操作します。
- `preserve`: 原調の音名を保持します。音域に収めるためのオクターブ移動は許可します。
- `auto-transpose`: 音域への収まりを考慮して曲全体の移調を許可します。移調量は曲全体で共通です。

曲中の操作なしで原調を弾くなら `fixed-preserve`、移調してもよければ `fixed-auto-transpose` を選びます。
導入や間奏で低い音域も使いたい場合は `switch` 版を選びます。実際の音域・移調量・切替位置は各版の編曲計画とレポートで確認してください。
GUIDE
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
    printf '\n## 聴き比べ\n\n' >>"$staging/README.md"
    comparison_heading=true
  fi
  case "$excerpt" in
  phrase) label='冒頭の主旋律' ;;
  harmony) label='コード変化部' ;;
  interlude) label='器楽間奏' ;;
  esac
  printf -- '- [%s](%s.mid)\n' "$label" "$file" >>"$staging/README.md"
done
cat >>"$staging/README.md" <<'GUIDE'

## 演奏と編集

- 25鍵固定版は曲全体で同じ音域、切替版は区間ごとに音域を変更します。目標MIDI音域と切替休符をレポートで確認して鍵盤を設定してください。
- MMLを編集した場合は再コンパイルと検証が必要です。移調や切替の計画ではコンパイル後の音符IDも更新します。
- 検証PASSは定義された条件への適合を示します。響きや実機での運指は試聴・演奏で確認してください。

ファイルの内容はこのフォルダで `sha256sum --check SHA256SUMS`（macOSでは `shasum -a 256 -c SHA256SUMS`）を実行して確認できます。
GUIDE
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
