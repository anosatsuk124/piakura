# 採譜の近似比較

`midieval reference.mid candidate.mid --json`は、採譜候補を参照MIDIへ近似照合する読み取り専用コマンド。`mididiff`の意味的な完全一致や`midistat`の旋律保持契約とは別の評価で、音楽性のPASS/FAILを出さない。

`--reference-channels 1,2`と`--candidate-channels 3`は1始まり。省略は全チャンネル、CH10は既定で除外（`--include-drums`で含める）。他のパーカッションbankやモデル固有の楽器分類は自動除外しないため、役割を確認してチャンネルを選ぶ。楽器番号・velocityは一致条件に含めない。曖昧な同音ペアと非正の音長は評価を拒否する。元SMFの警告はJSONに残る。

音高と開始秒（既定±0.05秒、`--onset-tolerance`で指定）から最大一対一マッチングを行う。PPQNとテンポ変化はSMFごとに秒へ変換する。同じ参照音に複数候補を一致させない。音長付きの指標は終了秒の差が参照音長の20%または50msの大きい方以内であることも要求する。これは[MIR評価の一般的な基準](https://mir-eval.readthedocs.io/latest/api/transcription.html)に沿った独立実装で、mir_evalの数値丸めまで同一ではない。

`pitch_onset`、`pitch_onset_offset`は適合率・再現率・F1と一致音数。`pitch_class_onset`はオクターブを無視した診断値で、主指標へ代用しない。`sounding_pitch_class_jaccard`は発音中pitch class集合の積集合/和集合を、有音区間の長さで加重平均する。和声機能の正しさを示さず、無音は分母に含めない。両側空のF1、候補空の適合率、参照空の再現率はnull。平均誤差は一致した音だけに対する値。

## 異なる編集版・演奏の時間対応

`--alignment alignment.json`は候補秒から参照秒への区間内線形補間を与える。各区間には最低2つのアンカーが必要。秒は非負有限値、各区間内で両時間軸が厳密増加し、区間同士は両時間軸で順序を保ち重ならない。繰り返しの別箇所への再対応は別の比較として実行する。

```json
{
  "version": 1,
  "segments": [
    [
      {"reference_seconds": 12.0, "candidate_seconds": 0.0},
      {"reference_seconds": 24.0, "candidate_seconds": 12.1},
      {"reference_seconds": 36.0, "candidate_seconds": 24.0}
    ]
  ]
}
```

共通区間とアンカーは音声・フレーズ・拍から確認し、全モデルの比較に同じものを使う。候補ごとの音符一致を最大化するためにアンカーを調整しない。区間をまたいだ補間と外挿は行わない。開始が区間内（先頭を含み末尾を含まない）の音を評価し、外の音数を別途報告する。区間より前に始まった持続音はこの選択に含まれない。末尾を越える音は和声集計で切り詰め、音長付き一致には数えず、平均音長誤差から除く。

整列なしは同じ秒タイムラインとみなす。時間対応が不明なら結果を採譜精度として解釈しない。入力/指定エラーはexit 2、評価成功は精度にかかわらずexit 0。`-o`は入力・alignmentと異なるファイルへのatomic出力を行う。
