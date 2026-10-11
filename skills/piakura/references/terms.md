# Terms of use

TERMS_VERSION: 2026-10-12

Show the user the summary below in their language: translate it faithfully, adding, dropping or softening nothing, and keep names, licenses and links as they are. Ask them to accept, read the full text, or decline. Record acceptance only after an explicit yes, with `piakura terms accept --version 2026-10-12`; the record goes to the user's own settings, not a project's. When this version changes, ask again.

## Summary

- piakura is licensed under the Apache License 2.0 and comes with no warranty. Its command-line tools are distributed as binaries without their source code, so they are not open source for now; the license still lets you use and redistribute them.
- It bundles no machine-learning model weights. When you transcribe audio, the weights and Python packages are downloaded from their own publishers (Hugging Face, GitHub, PyPI, Google Drive) to this machine or to the SSH worker you choose. Each has its own license. Some forbid commercial use, one requires an access request, and some have conflicting or unverified license labels (table below). You are responsible for checking and following them.
- You must have the rights to the music you give piakura. Transcriptions and arrangements may be derivative works of the original; piakura grants no rights to them.
- When you give a URL, the audio is downloaded with yt-dlp. Follow the site's terms and your local law.
- Audio, scores and settings stay on this machine or the worker host you choose. piakura sends nothing elsewhere, except the downloads above and a paid audio-review service only if you explicitly turn one on.

## Models and their terms

| Model | Used for | Source | License as published | Status |
|---|---|---|---|---|
| YourMT3+ (YPTF.MoE+Multi noPS) | multi-instrument transcription | Hugging Face Space `mimbres/YourMT3` | GitHub repository: GPL-3.0; Space metadata: Apache-2.0 | conflicting labels |
| Basic Pitch | pitch/onset transcription | `basic-pitch` on PyPI (Spotify) | Apache-2.0, model included | published |
| MuScriptor small/medium | piano/score transcription | Hugging Face `MuScriptor/*` (gated) | CC BY-NC 4.0 with access conditions (non-commercial, contact sharing, input-rights representations, indemnity) | access request required |
| SheetSage2 | melody/harmony evidence | Hugging Face `m-a-p/SheetSage2` | CC BY-NC 4.0 | non-commercial |
| GAME | singing transcription | GitHub `openvpi/GAME` release | CC BY-NC-SA 4.0 | non-commercial |
| ROSVOT with RMVPE | singing transcription | GitHub and Google Drive | not stated in our records | unverified |
| Demucs (htdemucs, htdemucs_6s) | source separation | `demucs` on PyPI | code MIT; weight license not found | unverified |
| Mel-Band RoFormer guitar (becruily) | guitar separation | Hugging Face `becruily/mel-band-roformer-guitar` | owner permits non-commercial use; no license file | non-commercial |
| Beat This | beat tracking | `beat-this` on PyPI | not stated in our records | unverified |
| torchcrepe | pitch tracking | `torchcrepe` on PyPI | not stated in our records | unverified |

"Unverified" means we did not find a license for the weights; it is not a permission. This is not legal advice.

## Full text

The summary above is the full set of terms. The piakura README repeats it with acknowledgments of the software piakura builds on.
