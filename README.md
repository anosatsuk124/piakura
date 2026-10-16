![piakura: music you can actually play](brand/piakura-hero.svg)

[![Release](https://img.shields.io/github/v/release/anosatsuk124/piakura?include_prereleases&sort=semver)](https://github.com/anosatsuk124/piakura/releases)
[![License](https://img.shields.io/github/license/anosatsuk124/piakura)](LICENSE)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%28Apple%20silicon%29-blue)
![Agents](https://img.shields.io/badge/agents-Codex%20%7C%20Claude%20Code%20%7C%20OpenCode-blue)
[![Stars](https://img.shields.io/github/stars/anosatsuk124/piakura?style=social)](https://github.com/anosatsuk124/piakura/stargazers)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-support-FF5E5B?logo=kofi&logoColor=white)](https://ko-fi.com/anosatsuk124)

[日本語](README.ja.md)

piakura turns a song into piano arrangements you can play. It is a set of skills for coding agents, made for Codex and usable from Claude Code and OpenCode. Give it a MIDI file, an audio file or a link to a recording and answer a few questions. It delivers Easy, Medium and Hard two-hand piano versions as editable [SakuraMML](https://sakuramml.com/) and MIDI, and can open a review page where you listen, compare and comment.

## What it does

- **MIDI to piano.** Arranges the whole ensemble (melody, bass, harmony, characteristic accompaniment) for two hands at three levels. Supports 88 keys and smaller keyboards such as 25 keys, with a fixed range or octave switches at rests, in the original key or transposed.
- **Audio to MIDI first.** Transcribes a mixed recording with open models, then corrects the result against the recording's own evidence (beats, pitch, repeated phrases, harmony) and marks what stays uncertain.
- **Checked scores.** Every level is validated for hand spans, notes per hand, fast leaps and crossed hands, and for keeping the melody you chose. A failure is reported, never relabelled as done.
- **Review in a browser (optional).** A piano roll and staff notation (key signatures, chord names or degrees, following playback, editable with MuseScore-like keys) with the score text, A/B playback against the recording, comments on ranges and notes, and FLAC/MP4 export (falling notes, the score, or the score above the notes). Download a score as MusicXML for MuseScore or as LilyPond. Open it on a tablet through your tailnet if you use Tailscale.
- **A delivery folder.** MIDI and MML for each level and keyboard version, validation reports and checksums.

## Requirements

| | |
|---|---|
| System | Linux (x86_64, arm64) or macOS on Apple silicon. Transcription on Linux needs x86_64: on Linux arm64, transcribe on an x86_64 machine over SSH. Windows is not supported; WSL2 is untested. |
| Agent | [Codex CLI](https://learn.chatgpt.com/docs/cli), [Claude Code](https://code.claude.com/) or [OpenCode](https://opencode.ai/), and Node.js for `npx` |
| Always | bash, python3 3.8+ |
| Audio or a link | [mise](https://mise.jdx.dev/), ffmpeg, and about 20 GB of disk for model environments. A GPU is optional: an NVIDIA GPU on this machine or on an x86_64 Linux machine you can reach over SSH. |
| Review export | ffmpeg and fluidsynth; for video titles in Chinese, Japanese or Korean, fontconfig with a CJK font (for example Noto Sans CJK). A GPU video encoder is optional (VA-API or NVENC on Linux, VideoToolbox on macOS); without one, MP4 encodes on the CPU |

The agent checks these with `piakura doctor` and tells you how to install what is missing.

## Install

```bash
npx skills add anosatsuk124/piakura -a codex          # this project (.agents/skills)
npx skills add anosatsuk124/piakura -a codex -g       # every project (~/.agents/skills)
npx skills add anosatsuk124/piakura -a claude-code    # Claude Code (.claude/skills)
npx skills add anosatsuk124/piakura -a opencode       # OpenCode
```

Install all six skills together: `piakura` (the entry point), `piakura-transcription`, `piakura-readable-mml`, `piakura-arranger`, `piakura-review` and `piakura-upgrade` (which brings work from an older piakura up to date and writes a review as a package for keyroam) use each other. The command-line tools are downloaded on first use into `~/.local/share/piakura`, checked against the release's SHA-256 sums. The first run asks whether to also put the `piakura` command in `~/.local/bin` (one link), so you can start the review page yourself; your shell profile is never changed. The skills CLI sends anonymous usage data; set `DISABLE_TELEMETRY=1` to turn that off.

## Use

| Agent | How to start |
|---|---|
| Codex | type `$piakura` (or choose it with `/skills`), optionally followed by a file path or URL |
| Claude Code | `/piakura [path or URL]` |
| OpenCode | ask it to use the piakura skill |

The first run:

1. shows the terms below and asks you to accept them;
2. installs the tools;
3. asks everything it needs in a few rounds: your input and your rights to it, where transcription should run, levels and keyboard, where to open the review page, where to write the results;
4. asks whether to keep your answers for this computer, for this project, or not at all;
5. starts the review page and gives you its address: you can watch each stage and the agent's notes arrive, then listen to the results and comment;
6. runs the work and records each stage in `piakura/work/<song>/piakura-job.json`, then writes the delivery to `piakura/dist/<song>/`.

If it stops, run `$piakura` again in the same project. It finds the job, answers any feedback you sent in the meantime first, and continues where it stopped.

### Where transcription runs

Only needed for audio or a link.

| Option | You need |
|---|---|
| This machine, directly (beginner-friendly) | mise. No separate server or Docker. Without an NVIDIA GPU it runs on the CPU, slowly. On macOS this is experimental. |
| An SSH host, directly | A Linux machine with an NVIDIA GPU, key-based SSH, Python 3.9+, mise and bubblewrap. Everything stays in one directory there; no sudo. |
| Docker (this machine or an SSH host), experimental | Docker and the NVIDIA Container Toolkit; while the image is private, `docker login ghcr.io`. Being in the `docker` group is equivalent to root on that machine. |

The agent asks before deploying anything to an SSH host. When the GPU is busy, it does what you chose: wait, stop and report, or use the CPU.

### Reviewing on a tablet

If Tailscale is installed and logged in, the agent can suggest serving the review page inside your tailnet with `tailscale serve`, so you can open it on a tablet or phone.

- This is `tailscale serve`, not `tailscale funnel`: only devices in your own tailnet can reach it, not the internet. It also gives the page the HTTPS it needs for playback.
- The review page has no login of its own. Anyone your tailnet's access rules allow, including shared users and devices, can open it.
- `piakura review stop` removes only the port piakura added (`tailscale serve --https=<port> off`). Do not use `tailscale serve reset`, which also removes your other serve settings.

piakura never offers funnel. If you ask for it, the agent explains that the page and your recording would be public on the internet and waits for your confirmation.

### Reviewing while no agent runs

The review page runs on its own; the agent does not need to be running. Feedback you submit is kept, and the next `$piakura` answers it before anything else. The page shows each stage, the agent's notes, and whether an agent is waiting for your feedback; a new result pops up with a Sync button.

```bash
piakura review start piakura/work/<song>    # prints the address; reports it if already running
piakura review status piakura/work/<song>   # address and unanswered feedback
piakura review stop piakura/work/<song>     # add --end when the review is over
piakura job next piakura/work/<song>        # what the agent will do next
```

The page comes back at the same address after a restart. If you did not put `piakura` on your PATH, use `~/.local/share/piakura/current/bin/piakura`.

## Settings

Answers you choose to keep go to `~/.config/piakura/config.json` (this computer) or `.piakura/config.json` (this project, at its Git root). Project settings override yours; `PIAKURA_*` environment variables override both. Your consent is kept only in your own settings, with the terms version and time. Secrets such as Hugging Face tokens are never stored.

```bash
piakura config resolve      # every effective value and where it came from
piakura config set arrangement.keys 25 --scope project
```

The agent runs these for you; the tools are in `~/.local/share/piakura/current/bin`, and in `~/.local/bin` if you chose the link.

Reports, score comments, notes and the delivery README are written in your system's language (`LANG`; English when piakura does not support it, currently anything but English and Japanese). The `language` setting (`en`, `ja`) or `PIAKURA_LANGUAGE` chooses another. The review page follows each viewer's browser language; its settings can change it. The agent talks to you in the language you write in.

## Output

```text
piakura/dist/<song>/
├── README.md               links to every version and report
├── easy.mid  easy.mml       (medium, hard alike)
├── keyboard/<mode>/        versions for a smaller keyboard
├── reports/  plans/        validation reports and arrangement plans
├── report.md               notes for playing
└── SHA256SUMS
```

Working files, including the recording and your review, stay in `piakura/work/<song>/`. Inside a Git repository, the agent offers to add both folders to `.gitignore`, so copyrighted material stays out of commits.

## Updating and removing

`npx skills update` updates the skills; the next run downloads the matching tools. To remove piakura, remove the skills (`npx skills remove`) and the `~/.local/bin/piakura` link if you chose it, and delete `~/.local/share/piakura`, `~/.config/piakura`, `~/.cache/piakura` (model environments, several GB) and `~/.local/state/piakura`. On an SSH host, delete the worker directory (default `~/piakura-worker`).

## Your data

Recordings, scores and settings stay on this machine or on the SSH host you choose. piakura has no telemetry. It connects to the network only to download the tools (GitHub), models and Python packages (Hugging Face, GitHub, PyPI, Google Drive) and the recording at a link you give (with yt-dlp). A paid audio-review service is used only if you explicitly turn one on.

## Limitations

- Transcription is evidence, not truth. Uncertain passages are marked in the reports instead of being guessed away.
- A passing validation means the score meets the defined limits for its level. Fingering, hand size and taste still need a player.
- Local transcription on macOS and the Docker worker are experimental.

## Source code and support

The skills in this repository are published with their source. The command-line tools are not open source yet: their source code is not tidy enough to publish, and we plan to open it later. If you find piakura useful or interesting, a star or a mention to others keeps us going and brings that day closer. If you would like to support it further, you can do so on [Ko-fi](https://ko-fi.com/anosatsuk124). None of this is needed to use piakura.

## Acknowledgments

piakura builds on:

- [SakuraMML](https://sakuramml.com/) and [sakuramml-rust](https://github.com/kujirahand/sakuramml-rust) by kujirahand (MIT), which compiles every score;
- the idea of SMF2MML, which inspired the MIDI-to-MML conversion (no code was used);
- [MuseScore_General](https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/) SoundFont (MIT) for playback;
- [gomidi](https://gitlab.com/gomidi/midi), the Go fonts and golang.org/x libraries; React, Base UI, shadcn/ui, CodeMirror, spessasynth, [VexFlow](https://www.vexflow.com/) (MIT) with the Bravura and Academico fonts (SIL OFL 1.1) and Fontsource fonts in the review page;
- the authors of the models listed below, [yt-dlp](https://github.com/yt-dlp/yt-dlp), [FFmpeg](https://ffmpeg.org/) and [FluidSynth](https://www.fluidsynth.org/).

The full notices ship with the tools as `THIRD_PARTY_NOTICES.md`.

## License and reservations

TERMS_VERSION: 2026-10-12

piakura is licensed under the [Apache License 2.0](LICENSE) and comes with no warranty. This applies to the skills in this repository and to the command-line tools in its releases alike. The tools are published as binaries only, without their source code, so they are not open source for now (see [Source code and support](#source-code-and-support)); the license still lets you use and redistribute them. The third-party software inside them keeps its own licenses, listed in `THIRD_PARTY_NOTICES.md`. You are asked to accept the following on first use.

**Model weights are not included.** When you transcribe audio, the weights and Python packages are downloaded from their publishers to your machine or SSH host. Each has its own terms, which you are responsible for checking and following:

| Model | Used for | License as published | Status |
|---|---|---|---|
| YourMT3+ | multi-instrument transcription | GitHub repository: GPL-3.0; Hugging Face Space: Apache-2.0 | conflicting labels |
| Basic Pitch | pitch and onset transcription | Apache-2.0 (weights in the package) | published |
| MuScriptor small/medium | piano transcription | CC BY-NC 4.0 with access conditions (non-commercial use, contact sharing, input-rights representations, indemnity) | access request required |
| SheetSage2 | melody and harmony evidence | CC BY-NC 4.0 | non-commercial |
| GAME | singing transcription | CC BY-NC-SA 4.0 | non-commercial |
| ROSVOT with RMVPE | singing transcription | not stated in our records | unverified |
| Demucs | source separation | code MIT; weight license not found | unverified |
| Mel-Band RoFormer guitar (becruily) | guitar separation | owner permits non-commercial use; no license file | non-commercial |
| Beat This | beat tracking | not stated in our records | unverified |
| torchcrepe | pitch tracking | not stated in our records | unverified |

If you say your use is commercial or undecided, piakura leaves out the non-commercial models and asks before using any whose license is conflicting or unverified. "Unverified" means we found no license for the weights; it is not a permission.

**Your music.** You need the rights to the music you give piakura. Transcriptions and arrangements may be derivative works of the original; piakura grants no rights to them. When you give a link, follow the site's terms and your local law.

This is not legal advice.
