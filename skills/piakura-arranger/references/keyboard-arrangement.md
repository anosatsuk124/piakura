# 鍵盤数・音域・調の指定

Skillは`keys=N`、`lowest-note=auto|MIDI番号`、`range-mode=fixed|switch`、`key-policy=preserve|auto-transpose`を受け取る。既定は88鍵/MIDI21〜108/fixed/preserve。25鍵指定時は最低音を自動提案する。鍵盤数は黒鍵を含む連続した半音の数で、25鍵の最高音は最低音+24。

autoの音域選択と編曲はSkillが行う。旋律の輪郭、句単位のオクターブ移動、和声の性格、保持中の左右配置と半音衝突を考慮する。フレーズと和声区間ごとに音域・旋律・伴奏を一緒に選び、伴奏の配置/分散/音数/離鍵を組み直す。詳細はSkillの[配置判断](voicing.md)と[検証契約](voicing-contract.md)を参照。DMK-25 PRO向けの推奨最低音はMIDIのC（12の倍数）から選ぶ。最低音の明示指定はそれ以外の音名も許可する。初期OCT設定が不明なら、目標MIDI音域を記録し、実機の現在値や必要なボタン操作回数は未確認とする。

preserveはpitch classを保ち、必要なオクターブ移動を許す。auto-transposeは曲全体で一つの半音移調量（-12〜12）を選ぶ。移調による旋律の変化を最小限にし、区間ごとに別の調へ変えない。

fixedは曲全体で同じN鍵を使う。switchは区間ごとに12半音単位で最低音を切り替える。切替には両手の離鍵、CC64/66の解除、最低2秒を満たす整数拍の休符が必要。テンポ/拍子と後続イベントも追加休符ぶん移動する。切替Markerを休符の開始に置く。Markerを表示しないプレイヤーではレポートの切替表を使う。

## 検証CLI

固定音域だけを検証する場合:

```bash
bash scripts/tool.sh midistat "$WORK/easy.mid" --profile easy --hands RH=1,LH=2 \
  --piano-mode solo --keys 25 --lowest-note 60 --require-pass
```

オクターブ移動、移調、切替休符を原曲と比較する場合:

```bash
bash scripts/validate.sh \
  "$WORK/easy.mid" easy "$WORK/easy-report.json" \
  "$WORK/source.mid" 1 --arrangement-plan "$WORK/easy-plan.json"
```

## ArrangementPlan v1

JSONは16MiB以内。未知フィールド・複数JSON・不正な値は入力エラー（exit2）。計画がある場合はその鍵盤設定を使い、明示したCLIのkeys/lowest-noteと矛盾すれば拒否する。元曲/出力の完全な時間軸を覆う区間を順番に記録する。区間内はPPQN換算以外の時間伸縮を許可しない。

```json
{
  "version": 1,
  "source_ppqn": 480,
  "output_ppqn": 480,
  "keys": 25,
  "range_mode": "switch",
  "key_policy": "preserve",
  "transpose_semitones": 0,
  "sections": [
    {"name":"section-01","source_start_tick":0,"source_end_tick":960,
     "output_start_tick":0,"output_end_tick":960,"lowest_note":48},
    {"name":"section-02","source_start_tick":960,"source_end_tick":1920,
     "output_start_tick":2880,"output_end_tick":3840,"lowest_note":60}
  ],
  "melody_mapping": [
    {"source":{"track":0,"on_order":10},"output":{"track":1,"on_order":20}},
    {"source":{"track":0,"on_order":12},"omit_reason":"Easy: repeated ornament omitted"}
  ]
}
```

この例の切替Markerはtick960に`Maker("piakura:range:60:84")`。固定したupstreamの命令名は`Maker`（`Marker`は構文エラー）。120BPMなら1920tickの休符は2秒。各区間にMMLの`@section`、`@keyboard-range`、切替に`@octave-switch`、冒頭に`@transpose`を残す。

`melody_mapping`は選択した原曲旋律の全音符について、出力先または省略理由を一つ記録する。track/on_orderはSMFの0始まりトラックとNoteOnイベント順序で、`smf2sakura --no-split-channels --report`のnotesから取得する。MMLを再コンパイルしたら出力IDも再確認する。

検証器は出力音符の実在、開始tick、移調を補正したpitch class、同じ出力音符を複数の原曲音符へ割り当てていないことを確認する。補正後保持率を別項目に記録し、Medium/Hardは100%を要求する。Easyの省略も全件明示する。参照MIDIがなければ時刻対応と調の検証はUNKNOWN。

検証PASSは実機のOCT設定、運指、音楽としての自然さの保証ではない。実機に目標音域を設定して演奏する必要がある。

Skillの標準検証は`--preserve-melody`を使い、省略を認めず押鍵時間もPPQN換算で保持する。ArrangementPlan v1の`omit_reason`は明示的に旋律を簡略化した分析にも使えるが、この保持契約を免除しない。音高/開始が合うだけで音長の変更を見逃さない。
