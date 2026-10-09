# 声部配置と例外の検証

`midistat --check-voicing`は、左右の配置と同時半音を検査する。Skillのvalidate/compareは常にこの検査と`--require-pass`を使う。単独のmidistatは従来どおり任意指定。鍵盤数やsolo/splitに関係なく同じ規則を使う。

- `hand_crossing`: 実際に保持しているLHの音がRHの音より高い音符ペア。
- `close_interval`: 同じ手または異なる手で、保持区間が重なり、実音高が1半音だけ離れたペア。pitch classの差だけでは判定しない。

重なりは`[max(start), min(end))`。ゼロ長音符は除外し、同tickの終了/開始は重なりに数えない。長い和音の途中に入る旋律も調べる。ペダル残響はこの押鍵検査へ加算せず、響きの確認で別に扱う。shared-keyの離鍵条件は[piano-output.md](piano-output.md)を引き続き適用する。

JSONの`voicing`に`score_sha256`、任意の`reference_sha256`、`detected`、`accepted`、`unresolved`、`issues`を出す。issuesは先頭200件、カウントは全件。各issueはrule/start_tick/end_tickと2音のref（track/on_order）・hand・pitchを持つ。未承認のペアはhard violationになりFAILとなる。手の所属が不明なら従来のUNKNOWNを維持する。

## VoicingReview v1

交差は、声部の受け渡しや意図した対話など具体的な音楽的理由を持つ場合だけ承認する。「25鍵へ収めるため」だけでは理由にならない。半音は、原曲で同時に存在した実音程1半音の不協和を保持する場合だけ承認できる。広い音程をオクターブ圧縮してできた隣接音は組み直す。

`--voicing-review "$WORK/easy-review.json"`で指定する。以下のハッシュは実際の`sha256sum`、音符IDはコンパイル後の`smf2sakura --no-split-channels --report`から取得する。

```json
{
  "version": 1,
  "score_sha256": "<compiled MIDI SHA256>",
  "exceptions": [
    {
      "rule": "hand_crossing",
      "notes": [{"track":1,"on_order":12},{"track":2,"on_order":8}],
      "reason": "左手の応答旋律を上声へ受け渡し、右手は下声の持続音を担当する。"
    }
  ]
}
```

`close_interval`にはreview直下の`reference_sha256`と例外内の`source_notes`（原曲の2音のtrack/on_order）も必要。source_notesはnotesと同じ対応順とし、宣言された全体移調を補正したpitch classが一致すること、原曲でも実音程1半音で重なること、PPQN/切替休符を補正した原曲の重なり区間が出力の重なり全体を覆うことを検証する。

未知フィールド、16MiB超、複数JSON、未知version、ハッシュ不一致、存在しない/同一/重複したペア、検出事項に一致しない規則、空の理由、不適切な出典は入力エラー（exit2）。既存レポートを置き換えない。再コンパイル後は例外のIDとハッシュを更新し、理由も再確認する。無効なreviewを分析APIへ直接渡した場合も例外を承認しない。

例外は当該ペアと規則だけに適用し、音域・手ごとの能力・共有鍵・旋律保持を免除しない。ArrangementPlan v1の構造は変更しない。レビューは編集可能な別スコアではない。

機械検査は理由の音楽的妥当性、和声の機能、声部進行、ペダルの濁りを証明しない。原曲の該当区間と完成MIDIを照合し、意図した例外だけが残ることを確認する。Skillの完了には、この照合と検証PASSの両方が必要。
