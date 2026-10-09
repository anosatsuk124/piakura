# ピアノ検証の確定仕様

`midistat`は既定で88鍵ピアノ（MIDI 21〜108）を使い、`--keys N --lowest-note MIDI`または[編曲計画](keyboard-arrangement.md)で指定した音域について、キーを押している区間と発音開始を分析する。サステインによる残響は指の占有に数えない。終了と開始が同じtickなら終了を先に扱う。

## 手の指定と判定

`--hands RH=1,LH=2`はコンパイル後のSMFトラック番号（0始まり）を指定する。複数トラックは`RH=1+3,LH=2`。全音符の所属が確定した場合だけPASSを返せる。省略時はMIDI 60以上をRH、未満をLHとして参考値を計算し、UNKNOWNとする。未対応の音符、同音重複の曖昧さ、未終了音などもUNKNOWNの理由になる。

|profile|同時押鍵数/手|同時押鍵の幅|250ms以内の跳躍|元曲に対する音数の目安|
|---|---:|---:|---:|---|
|easy|3|12半音|12半音以下|25〜45%|
|medium|4|14半音|警告|45〜70%|
|hard|5|警告（14半音超）|警告|70〜90%|

跳躍は連続する発音群の最低音同士・最高音同士の移動の最大値。所要時間はテンポ変化を積分する。音数、幅、跳躍の違反はtickと手を記録する。上表のhard constraintを満たすことは、実際の運指・体格・練習量を含めた演奏可能性の保証ではない。難易度の閾値は設計上の初期値で、実演による校正は未実施。

Easyの最大1秒音密度RH4音/LH2音とLH発音間隔2拍は警告の目安。Profile JSONの`max_rh_notes_per_second`、`max_lh_notes_per_second`、`min_lh_onset_beats`も警告閾値として扱う。和音は構成音ごとに密度へ数えるため、この値をhard constraintにすると和声を失う。主旋律の音高・リズム・音価を優先し、伴奏の重複・内声・追加フィルを減らす。LHは2音を基本に必要な箇所で3音を使い、根音に3度/7度などを組み合わせて和声の性格を保つ。伴奏の保持時間は次の発音・和声変化・句末に合わせる。裏拍、連打、短いgateだけで装飾と判定しない。

## 参考指標

平均/最大1秒音密度、最大同時押鍵、最大幅、最大高速跳躍、連打、16分グリッド外の発音率、和音発音率、同時オクターブ対を記録する。幅は同じ手で保持する全キーの最高音−最低音。密度・連打・リズムは警告材料で、未校正の総合点へ換算しない。

## 原曲との比較

`--reference original.mid --melody-channels 1`のチャンネルは原曲の1始まりMIDIチャンネル。旋律保持率は指定チャンネルの音高と発音tickを四分音符単位で照合する。テンポを見ないため、参照と楽譜のテンポマップや拍子が違うと警告する。readableで書いた編曲は、同じ時計で量子化したreadable参照（このスキルの`scripts/readable-reference.sh`）と照合する。移調・オクターブ移動は一致に数えない。編曲計画がなければmedium/hardは厳密な100%保持を要求する。計画があれば、宣言された全体移調・オクターブ移動・追加休符を補正した保持率を別に計算し、medium/hardは補正後100%を要求する。厳密な保持率も残す。easyの保持率は報告値とする。指定なしの旋律保持率は未知。

`--preserve-melody`は参照と旋律チャンネル指定を必須にし、全音符の音高・開始・押鍵時間を要求する。欠落は`melody_missing`、保持音の押鍵時間変更は`melody_duration_changed`でFAIL。Skillの参照付きvalidate/compareは既定でこの契約を使う。省略理由を計画へ書いても免除されない。ユーザーが旋律の簡略化を認めた場合は、[Skillの手順](rhythm-and-articulation.md)に従い、元の採譜と別に変更範囲・置換音符を宣言した保持契約を作る。その契約に対する厳密検証と元参照との差分を併記し、元旋律100%保持とは表現しない。検証器の判定は変更しない。未指定時は上記の従来判定を維持する。

`melody_duration_matched`と`melody_duration_preservation`は音高・開始・押鍵時間がすべて一致する音符の数/率。計画がある場合は`adjusted_melody_duration_matched`と`adjusted_melody_duration_preservation`も出す。押鍵時間はPPQNの整数積で比較し、切替休符を加算しない。音符が区間終端ちょうどに終了する場合も同じ規則を使う。velocityはこのフラグの判定対象に含めない。

音数比は原曲の有音高音符を分母にする。打楽器はCH10またはNoteOn時のbank MSB 126/127として参考分類する（GM/XG向けのヒューリスティック）。機器独自のbank分類は解釈しない。和声カバー率は四分音符ごとの発音pitch class集合、リズム類似率は有音高の発音時刻集合の再現率。コード機能や声部進行の正しさを表す指標ではない。

JSONにprofile、status（PASS/FAIL/UNKNOWN）、unknown_reasons、hard_violation_count、violations、warnings、全体/各手のmetrics、任意のpreservationを出す。violation明細は先頭200件まで、総数は省略しない。FAILを優先し、hard違反がなくても未知条件があればUNKNOWN。exit 0はPASSまたは参考分析のUNKNOWN、exit 1はFAIL、exit 2は使用法/入力エラー。Skillはexit値だけでなくstatusを確認する。

`--require-pass`を指定するとUNKNOWNもexit 1になる。Skillのvalidate helperはこの指定を使う。

Skillのvalidate/compareは`--check-voicing`も必須にする。保持区間の左右交差と実音程1半音を検出し、具体的な音符ペアと原曲の出典に結び付く例外だけを許す。判定・JSON・例外の契約は[声部配置](voicing-contract.md)を参照。従来の単独midistat分析ではこの検査を明示指定する。
