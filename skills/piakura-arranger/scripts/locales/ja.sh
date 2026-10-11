# shellcheck shell=bash
# The delivery README in Japanese; export.sh sources it. Every language
# defines the same msg_ functions (docs/i18n.md).

msg_intro() {
  cat <<'TEXT'
# ピアノ演奏用MIDI

MIDIを開いて演奏・再生できます。編集用のSakuraMMLはMIDIの隣にあります。
通常版から始め、小型鍵盤では鍵盤モードに合う25鍵版を選んでください。
音域・移調・切替位置・検証結果は各ファイルのレポートと編曲計画で確認できます。

|版|Easy|Medium|Hard|
|---|---|---|---|
TEXT
}

# msg_link report|plan|review: the name of a score's sidecar link.
msg_link() {
  case "$1" in
  report) printf '検証' ;;
  plan) printf '計画' ;;
  review) printf '配置の例外' ;;
  esac
}

# msg_group standard|<range-mode>-<key-policy>: a row of the table.
msg_group() {
  # The backticks are literal Markdown code spans.
  # shellcheck disable=SC2016
  case "$1" in
  standard) printf '通常版' ;;
  fixed-preserve) printf '25鍵・固定・原調（`fixed-preserve`）' ;;
  fixed-auto-transpose) printf '25鍵・固定・移調（`fixed-auto-transpose`）' ;;
  switch-preserve) printf '25鍵・切替・原調（`switch-preserve`）' ;;
  switch-auto-transpose) printf '25鍵・切替・移調（`switch-auto-transpose`）' ;;
  esac
}

msg_report_link() { printf '編曲結果・演奏条件・切替表'; }

msg_keyboard_guide() {
  cat <<'TEXT'

## keyboard/の名前と選び方

フォルダ名は `<range-mode>-<key-policy>` です。

- `fixed`: 曲全体で同じ25鍵を使い、曲中のOCT切替を行いません。演奏前には目標音域へ設定します。
- `switch`: 区間ごとに実機のOCT設定を変更します。最低2秒の操作用休符があり、レポートの切替表に従って操作します。
- `preserve`: 原調の音名を保持します。音域に収めるためのオクターブ移動は許可します。
- `auto-transpose`: 音域への収まりを考慮して曲全体の移調を許可します。移調量は曲全体で共通です。

曲中の操作なしで原調を弾くなら `fixed-preserve`、移調してもよければ `fixed-auto-transpose` を選びます。
導入や間奏で低い音域も使いたい場合は `switch` 版を選びます。実際の音域・移調量・切替位置は各版の編曲計画とレポートで確認してください。
TEXT
}

msg_comparisons() { printf '聴き比べ'; }

# msg_excerpt phrase|harmony|interlude: an excerpt to compare.
msg_excerpt() {
  case "$1" in
  phrase) printf '冒頭の主旋律' ;;
  harmony) printf 'コード変化部' ;;
  interlude) printf '器楽間奏' ;;
  esac
}

msg_playing() {
  cat <<'TEXT'

## 演奏と編集

- 25鍵固定版は曲全体で同じ音域、切替版は区間ごとに音域を変更します。目標MIDI音域と切替休符をレポートで確認して鍵盤を設定してください。
- MMLを編集した場合は再コンパイルと検証が必要です。移調や切替の計画ではコンパイル後の音符IDも更新します。
- 検証PASSは定義された条件への適合を示します。響きや実機での運指は試聴・演奏で確認してください。

ファイルの内容はこのフォルダで `sha256sum --check SHA256SUMS`（macOSでは `shasum -a 256 -c SHA256SUMS`）を実行して確認できます。
TEXT
}
