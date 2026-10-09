# 演奏用出力の契約

`bash scripts/export.sh "$WORK" "$DELIVERY"`は、コンパイル・検証済みの作業ディレクトリ（`$WORK`）から演奏用ファイルを納品先（`$DELIVERY`）へまとめる。編曲・コンパイル・検証を行うコマンドではなく、完成したファイルの出力先を整える。

```text
$DELIVERY/
├── README.md                 # 各版のMIDI/MML/検証/計画へのリンク
├── easy.mid / easy.mml       # 通常版（Medium/Hardも同様）
├── keyboard/<mode>/          # 25鍵のfixed/switch × preserve/auto-transpose
├── reports/                 # 検証JSON、通常版とkeyboard/を同じ構成で格納
├── plans/                   # 編曲計画JSON、同じ構成
├── reviews/                 # 任意の声部配置例外JSON、同じ構成
├── comparisons/easy/        # phrase/harmony/interludeの比較用MIDIとMML
├── report.md                # 任意の編曲結果・演奏条件・切替表
├── SHA256SUMS
└── .piakura-dist
```

各levelのMIDI/MMLは対で必要。存在するlevelだけを出力し、report/plan/reviewと比較用ファイルは存在すれば含める。通常版と4種類の鍵盤フォルダを明示的に列挙し、原曲、旧版、私的な編曲スクリプト、decisions JSONは`$WORK`に保持する。report.mdは`$WORK/arrangement-report.md`をそのままコピーするため、本文の相対リンクはこの出力構成に合わせて記述する。

全ファイルを別ディレクトリへ作成してから出力先を置換する。不完全なMIDI/MMLの対などで失敗した場合は前回の出力を維持する。入力/出力の包含・同一パス、出力先symlink、所有Markerのない既存出力先は拒否する。既存の配布フォルダへの更新は再生成扱いで、出力先だけで加えた編集は引き継がない。

成果物の内容一致は出力先で`sha256sum --check SHA256SUMS`を実行して確認する。Gitはdist全体を除外する。検証の合格や音楽的な判断はコピー処理では再評価しない。
