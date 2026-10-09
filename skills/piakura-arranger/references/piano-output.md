# ピアノ出力

編曲の標準`solo`はTR0指揮、TR1右手、TR2左手で、両手CH1。`split`は右手CH1、左手CH2。同じチャンネルでも左右のトラックと手の指定は維持する。SMFのTrackNameにもRight hand/Left handを記録し、音色はVoice(1,0,0)を使う。

`midistat --piano-mode solo|split`で構成を検証する。省略時は既存CLIとの互換性のためチャンネル構成を検証しない。Skillのvalidate/compare helperはsoloを既定値にし、末尾の`--piano-mode split`で変更できる。

soloでは同音重複と異なるトラック間の同tick引継ぎを拒否する。同じ手に複数トラックを割り当てた場合も同じ条件を適用する。SMFの異なるトラック間には全プレイヤー共通の同tick実行順序がなく、先にNoteOnを送ると別トラックのNoteOffが切断し得る。引継ぎ前に最低1tickの離鍵間隔を設ける。検証器が音符を切り詰めることはない。

音色、bank、CC、pitch bend、ペダルはチャンネルの共有状態。ピアノ以外のprogram/bankと、異なるトラックが同tickに送る矛盾した共有設定はFAILにする。左右別の音量やペダルを意図する場合はsplitを使う。

`smf2sakura --no-split-channels`は入力トラック内のチャンネル切替を保持する。ピアノソロ化は編曲後のMMLのCH指定で行う。

Neothesiaで自動試聴するときは両手のトラックをAutoにする。Humanは練習者の入力を待つ設定、Muteは再生しない設定。MIDIのCH指定とは独立している。Synthesiaも左右を別トラックで識別できる。[制作者向け公式ガイド](https://synthesiagame.com/support/guide/contentCreators)。
