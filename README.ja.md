![piakura: 弾けるピアノ編曲](brand/piakura-hero.svg)

[![Release](https://img.shields.io/github/v/release/anosatsuk124/piakura?include_prereleases&sort=semver)](https://github.com/anosatsuk124/piakura/releases)
[![License](https://img.shields.io/github/license/anosatsuk124/piakura)](LICENSE)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%28Apple%20silicon%29-blue)
![Agents](https://img.shields.io/badge/agents-Codex%20%7C%20Claude%20Code%20%7C%20OpenCode-blue)
[![Stars](https://img.shields.io/github/stars/anosatsuk124/piakura?style=social)](https://github.com/anosatsuk124/piakura/stargazers)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-support-FF5E5B?logo=kofi&logoColor=white)](https://ko-fi.com/anosatsuk124)

[English](README.md)

piakura は、曲を弾けるピアノ編曲にするためのツールです。コーディングエージェント用のスキル一式として作られています。主な対象は Codex で、Claude Code と OpenCode からも使えます。MIDI ファイル・音源ファイル・録音の URL のどれかを渡し、いくつかの質問に答えると、両手ピアノの Easy・Medium・Hard の3つの難易度を、編集できる [SakuraMML](https://sakuramml.com/) と MIDI で納品します。ブラウザで聴き比べてコメントできるレビュー画面も開けます。

## できること

- **MIDI からピアノ編曲。** 主旋律・ベース・和声・特徴的な伴奏を含む曲全体を、両手の3つの難易度に編曲します。88鍵のほか25鍵などの小さな鍵盤にも対応します。音域は固定にも、休符でオクターブを切り替える形にもでき、原調のままにも移調にもできます。
- **音源なら先に採譜。** 混合音源を公開モデルで採譜し、その録音自体の根拠（拍、音高、繰り返される句、和声）で結果を直します。確かめられない箇所は、不確かなまま印を付けて残します。
- **検査済みの楽譜。** 難易度ごとに、手の幅、片手の同時音数、速い跳躍、左右の交差と、選んだ主旋律が保たれているかを検査します。検査に通らなければ、そのまま報告します。完了扱いにはしません。
- **ブラウザでのレビュー（任意）。** ピアノロールと五線譜（調号、コードネームかディグリー、再生への追従、MuseScore に近いキー操作での編集）と楽譜のテキスト、録音とのA/B再生、範囲や音符へのコメント、FLAC/MP4 の書き出し（落ちてくる音符、楽譜、または楽譜とその下の落ちてくる音符）ができます。楽譜は MuseScore 向けの MusicXML や LilyPond でダウンロードできます。Tailscale を使っていれば、tailnet 経由でタブレットからも開けます。
- **納品フォルダ。** 難易度と鍵盤の版ごとの MIDI と MML、検査レポート、チェックサムをまとめます。

## 必要なもの

| | |
|---|---|
| OS | Linux（x86_64、arm64）、または Apple silicon の macOS。Linux での採譜は x86_64 が必要です。Linux の arm64 では、SSH で入れる x86_64 のマシンで採譜します。Windows は対象外で、WSL2 は未検証です。 |
| エージェント | [Codex CLI](https://learn.chatgpt.com/docs/cli)、[Claude Code](https://code.claude.com/)、[OpenCode](https://opencode.ai/) のどれか。`npx` のために Node.js |
| 常に | bash、python3 3.8 以上 |
| 音源・URL から始める場合 | [mise](https://mise.jdx.dev/)、ffmpeg、モデルの環境に約 20 GB の空き容量。GPU は任意です。このマシンの NVIDIA GPU か、SSH で入れる x86_64 の Linux マシンの NVIDIA GPU を使えます。 |
| レビューの書き出し | ffmpeg と fluidsynth。動画の見出しに中国語・日本語・韓国語を使うときは、fontconfig と CJK フォント（Noto Sans CJK など）。GPU の動画エンコーダー（Linux は VA-API か NVENC、macOS は VideoToolbox）は任意で、ないときは MP4 を CPU でエンコードします |

エージェントが `piakura doctor` で確かめ、足りないものの入れ方を案内します。

## インストール

```bash
npx skills add anosatsuk124/piakura -a codex          # このプロジェクトに（.agents/skills）
npx skills add anosatsuk124/piakura -a codex -g       # すべてのプロジェクトに（~/.agents/skills）
npx skills add anosatsuk124/piakura -a claude-code    # Claude Code（.claude/skills）
npx skills add anosatsuk124/piakura -a opencode       # OpenCode
```

5つのスキルはまとめて入れてください。入口の `piakura` と、`piakura-transcription`・`piakura-readable-mml`・`piakura-arranger`・`piakura-review` は互いを参照しています。コマンドラインのツールは初回に `~/.local/share/piakura` へ取得され、リリースの SHA-256 で検証されます。初回には、`piakura` コマンドを `~/.local/bin` にも置くか（リンクを1つ作ります）を尋ねます。置くと、レビューのページを自分で起動できます。シェルの設定ファイルは変更しません。skills CLI は匿名の利用データを送ります。止めるには `DISABLE_TELEMETRY=1` を設定します。

## 使い方

| エージェント | 始め方 |
|---|---|
| Codex | `$piakura` と入力します（`/skills` から選んでもかまいません）。続けてファイルのパスか URL を書けます |
| Claude Code | `/piakura [パスか URL]` |
| OpenCode | piakura スキルを使うよう頼みます |

初回の流れ:

1. 下の利用条件を示し、同意を求めます。
2. ツールをインストールします。
3. 必要なことを数回に分けてまとめて聞きます。入力とその権利、採譜をどこで動かすか、難易度と鍵盤、レビューのページをどこで開くか、結果をどこに書くかです。
4. 答えを、このコンピューター用・このプロジェクト用のどちらに保存するか、保存しないかを聞きます。
5. レビューのページを起動し、アドレスを伝えます。各段階の進み具合とエージェントのメモが届くのを見られ、結果が出たら試聴してコメントできます。
6. 作業を進め、各段階を `piakura/work/<曲>/piakura-job.json` に記録し、納品物を `piakura/dist/<曲>/` に書き出します。

途中で止まったら、同じプロジェクトでもう一度 `$piakura` を実行します。job を見つけ、その間に送ったフィードバックに先に答えてから、止まったところから続けます。

### 採譜をどこで動かすか

音源か URL から始める場合だけ必要です。

| 選択肢 | 必要なもの |
|---|---|
| このマシンで直接（初心者向け） | mise だけです。別のサーバーも Docker も要りません。NVIDIA GPU がなければ CPU で動きます（遅くなります）。macOS では試験的な扱いです。 |
| SSH 先で直接 | NVIDIA GPU を積んだ Linux マシンと、鍵での SSH ログイン、Python 3.9 以上、mise、bubblewrap。SSH 先では1つのディレクトリの中だけで完結し、sudo は使いません。 |
| Docker（このマシンか SSH 先。試験的） | Docker と NVIDIA Container Toolkit。イメージが private の間は `docker login ghcr.io` が必要です。`docker` グループに入ることは、そのマシンで root と同じ権限を持つことになります。 |

SSH 先に何かを置く前に、エージェントが確認を取ります。GPU が使えないときは、選んだとおりに動きます。待つ、止めて報告する、CPU に切り替える、のどれかです。

### タブレットでレビューする

Tailscale が入っていてログイン済みなら、エージェントが「tailnet の中で `tailscale serve` を使って公開すれば、タブレットやスマートフォンでも開ける」と提案します。

- 使うのは `tailscale serve` で、`tailscale funnel` ではありません。届くのは自分の tailnet 内の端末だけで、インターネットには公開されません。再生に必要な HTTPS もこれで満たせます。
- レビュー画面自体にはログインがありません。tailnet の ACL が許す人や端末（共有した相手を含む）は開けます。
- `piakura review stop` は、piakura が足したポートだけを外します（`tailscale serve --https=<port> off`）。他の serve 設定まで消える `tailscale serve reset` は使いません。

piakura から funnel を提案することはありません。頼まれた場合は、画面と録音がインターネットに公開されることを説明し、確認を取ってから進めます。

### エージェントが動いていないときにレビューする

レビューのページは単独で動きます。エージェントを起動していなくても構いません。送ったフィードバックは保存され、次に `$piakura` を実行すると、ほかの作業より先に答えます。ページには、各段階の状態、エージェントのメモ、エージェントがフィードバックを待っているかが出ます。新しい結果が届くと、Sync ボタン付きの通知が出ます。

```bash
piakura review start piakura/work/<曲>    # アドレスを表示します。動いていればそのアドレスを返します
piakura review status piakura/work/<曲>   # アドレスと、まだ答えていないフィードバック
piakura review stop piakura/work/<曲>     # レビューを終えるときは --end を付けます
piakura job next piakura/work/<曲>        # エージェントが次にすること
```

起動し直しても、同じアドレスで開けます。`piakura` を PATH に置いていない場合は、`~/.local/share/piakura/current/bin/piakura` を使います。

## 設定

保存を選んだ答えは、`~/.config/piakura/config.json`（このコンピューター）か `.piakura/config.json`（このプロジェクト。Git のルートに置きます）に書かれます。プロジェクトの設定がユーザーの設定より優先され、`PIAKURA_*` 環境変数はさらに優先されます。同意の記録は、利用条件の版と時刻と一緒に、ユーザーの設定にだけ残ります。Hugging Face のトークンのような秘密情報は保存しません。

```bash
piakura config resolve      # 有効な値と、それぞれの出どころ
piakura config set arrangement.keys 25 --scope project
```

ふだんはエージェントがこれを実行します。ツールは `~/.local/share/piakura/current/bin` にあります。リンクを選んだ場合は `~/.local/bin` にもあります。

レポート、楽譜のコメント、メモ、納品の README は、システムの言語（`LANG`）で書かれます。piakura が対応していない言語（いまは英語と日本語以外）なら英語になります。別の言語にするには、設定の `language`（`en`、`ja`）か `PIAKURA_LANGUAGE` を使います。レビュー画面は、見る人のブラウザの言語で表示され、画面の設定で変えられます。エージェントは、あなたが書く言語で話します。

## 出力

```text
piakura/dist/<曲>/
├── README.md               各版とレポートへのリンク
├── easy.mid  easy.mml       （medium、hard も同じ）
├── keyboard/<mode>/        小さな鍵盤用の版
├── reports/  plans/        検査レポートと編曲計画
├── report.md               演奏のための説明
└── SHA256SUMS
```

録音やレビューを含む作業ファイルは `piakura/work/<曲>/` に残ります。Git リポジトリの中では、著作物をコミットに入れないよう、両方のフォルダを `.gitignore` に足すかどうかをエージェントが聞きます。

## 更新と削除

`npx skills update` でスキルを更新すると、次の実行で同じ版のツールが取得されます。削除するときは、スキルを外し（`npx skills remove`）、リンクを選んだ場合は `~/.local/bin/piakura` も消し、`~/.local/share/piakura`、`~/.config/piakura`、`~/.cache/piakura`（モデルの環境。数 GB）、`~/.local/state/piakura` を消します。SSH 先では、ワーカーのディレクトリ（既定は `~/piakura-worker`）を消します。

## データの扱い

録音・楽譜・設定は、このマシンか、利用者が選んだ SSH 先の中に留まります。piakura は利用状況を送信しません。ネットワークにつなぐのは、次を取得するときだけです。

- ツール（GitHub）
- モデルと Python パッケージ（Hugging Face、GitHub、PyPI、Google Drive）
- 利用者が渡した URL の録音（yt-dlp）

有料の音声確認サービスは、利用者が明示的に有効にした場合にだけ使います。

## 制限事項

- 採譜は根拠であって正解ではありません。不確かな箇所は推測で埋めず、レポートに印を付けて残します。
- 検査に通ったことは、その難易度で定めた限度に収まっていることを示します。運指や手の大きさ、好みは、弾く人の判断が要ります。
- macOS のこのマシンでの採譜と、Docker のワーカーは試験的な扱いです。

## ソースコードと応援

このリポジトリのスキルは、ソースのまま公開しています。コマンドラインのツールは、まだオープンソースではありません。ソースコードを公開できる形に整理しきれていないためで、いずれ公開する予定です。piakura が役に立ったら、あるいは面白そうだと思ったら、スターを付けたり、人に紹介したりしてもらえると励みになり、公開も早まります。[Ko-fi](https://ko-fi.com/anosatsuk124) で支援してもらえると、とてもうれしいです。どれも、piakura を使うために必要なことではありません。

## 謝辞

piakura は次のものの上に作られています。

- すべての楽譜をコンパイルする、kujirahand さんの [SakuraMML](https://sakuramml.com/) と [sakuramml-rust](https://github.com/kujirahand/sakuramml-rust)（MIT）
- MIDI から MML への変換の着想を得た SMF2MML（コードは使っていません）
- 再生に使う [MuseScore_General](https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/) SoundFont（MIT）
- [gomidi](https://gitlab.com/gomidi/midi)、Go フォントと golang.org/x のライブラリ。レビュー画面の React、Base UI、shadcn/ui、CodeMirror、spessasynth、[VexFlow](https://www.vexflow.com/)（MIT）と Bravura・Academico のフォント（SIL OFL 1.1）、Fontsource のフォント
- 下の表のモデルの作者、[yt-dlp](https://github.com/yt-dlp/yt-dlp)、[FFmpeg](https://ffmpeg.org/)、[FluidSynth](https://www.fluidsynth.org/)

告知の全文は、ツールと一緒に `THIRD_PARTY_NOTICES.md` として配布します。

## ライセンスと留保

TERMS_VERSION: 2026-10-12

piakura は [Apache License 2.0](LICENSE) で提供され、無保証です。このリポジトリのスキルにも、リリースのコマンドラインのツールにも、同じライセンスが適用されます。ツールはバイナリだけを公開し、ソースコードは公開していないので、今のところオープンソースではありません（[ソースコードと応援](#ソースコードと応援)）。ライセンスに従って、使うことも再配布することもできます。ツールに含まれる第三者のソフトウェアには、それぞれのライセンスが適用されます（`THIRD_PARTY_NOTICES.md`）。初回に次の内容への同意を求めます。

**モデルの重みは含みません。** 音源を採譜するとき、重みと Python パッケージは、それぞれの配布元から利用者のマシンか SSH 先に取得されます。重みごとに条件があり、確認して従うのは利用者の責任です。

| モデル | 用途 | 公表されているライセンス | 状況 |
|---|---|---|---|
| YourMT3+ | 多楽器の採譜 | GitHub のリポジトリは GPL-3.0、Hugging Face の Space は Apache-2.0 | 表示が食い違う |
| Basic Pitch | 音高と発音の採譜 | Apache-2.0（重みはパッケージに同梱） | 公表済み |
| MuScriptor small/medium | ピアノの採譜 | CC BY-NC 4.0 と利用条件（非商用、連絡先の共有、入力の権利の表明、補償） | 利用申請が必要 |
| SheetSage2 | 旋律と和声の根拠 | CC BY-NC 4.0 | 非商用 |
| GAME | 歌の採譜 | CC BY-NC-SA 4.0 | 非商用 |
| ROSVOT と RMVPE | 歌の採譜 | 記録なし | 未確認 |
| Demucs | 音源分離 | コードは MIT、重みのライセンスは見つかっていない | 未確認 |
| Mel-Band RoFormer guitar（becruily） | ギターの分離 | 作者が非商用での利用を許可。ライセンスファイルはない | 非商用 |
| Beat This | 拍の検出 | 記録なし | 未確認 |
| torchcrepe | 音高の追跡 | 記録なし | 未確認 |

用途を「商用」か「未定」と答えた場合、piakura は非商用のモデルを使いません。表示が食い違うモデルや未確認のモデルは、使う前に確認を取ります。「未確認」は、重みのライセンスが見つからなかったという意味で、許可ではありません。

**曲の権利。** piakura に渡す曲を使う権利は、利用者が持っている必要があります。採譜と編曲は原曲の二次的著作物になりえます。piakura はそれらの権利を与えません。URL を渡すときは、サイトの規約と各地の法律に従ってください。

これは法的な助言ではありません。
