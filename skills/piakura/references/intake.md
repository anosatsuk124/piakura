# Intake questions

Ask everything the run needs before starting it, in as few rounds as practical, in the user's language. Show defaults and what each option needs, take the user's answers literally, and never answer for them.

How to ask:

- With a question tool (Claude Code's AskUserQuestion, Codex's `request_user_input` when enabled): one round per call, at most four questions of two to four options each; the tool adds a free-text "other".
- Without one (Codex's default mode): ask R0 alone, then send R1–R5 together as one numbered form with each default filled in ("reply `defaults`, or the numbers to change"), then ask R6. Ask again only for answers that are missing or invalid.
- Skip a question whose answer is already known: from the invocation argument, the saved settings the user chose to reuse (R1), or an earlier answer.
- Before R3, run `piakura doctor --json` (add `--transcription`, and `--review` before R5) and reflect what is installed in the option descriptions; do not offer GPU options a machine cannot use.

## R0 Consent

Only when `piakura terms status --version <TERMS_VERSION>` fails (or the tools are not installed yet). Show the summary from [terms](terms.md).

- Accept: continue; the acceptance is stored in the user's own settings with the terms version and time.
- Show the full text: show all of terms.md, then ask again.
- Decline: stop and tell the user that nothing was installed or saved.

## R1 Saved settings

Only when `piakura config resolve --json` shows `user` or `project` values. Summarize them.

- Use them as they are
- Review them (ask the affected questions with the saved values as defaults)
- Not this time (use defaults; keep the files unchanged)

## R2 Input

1. What do you have? A MIDI file a person made / MIDI from automatic transcription (noisy) / an audio file of the mixed song / a URL of the song.
2. Its path or URL (prefill from the invocation argument).
3. Confirm the rights: "I have the rights to use this music for this purpose." For a URL add: "and downloading it follows the site's terms." Without a yes, stop.
4. Title, artist and version or edit (optional; used to look up the recording's metadata).

For MIDI from automatic transcription, also ask whether the original recording is available; it becomes audio evidence.

## R3 Transcription (audio, URL, or model MIDI with its recording)

1. Where should the model run?
   - This machine.
   - An SSH host: a Linux machine with an NVIDIA GPU.
2. How should it run?
   - Directly on the host (beginner-friendly; list it first): only mise is needed, no container. Dependencies and models go into piakura's own cache directory and the system is left unchanged. An SSH host also needs Python 3.9+ and bubblewrap.
   - In a Docker container (experimental): Docker, plus the NVIDIA Container Toolkit for a GPU. Nothing like mise is installed on the host, but membership in the `docker` group amounts to root there; say so. While the image is private, the host must be logged in to `ghcr.io`.
3. Device, and what to do when the GPU is busy or fails: GPU (CUDA) or CPU (slow). When the GPU is unavailable: wait and retry / stop and report / switch to the CPU. Switching to the CPU only ever happens with this explicit permission. On macOS, offer the CPU on this machine (experimental) or an SSH host; there is no CUDA.
4. Use: personal or other non-commercial use / commercial or undecided. Commercial or undecided excludes the non-commercial models and warns about the conflicting and unverified licenses in [terms](terms.md). Also ask whether they have accepted MuScriptor's access conditions on Hugging Face (default: no; never accept for them).

Saved as `transcription.where`, `transcription.how`, `transcription.device`, `transcription.gpu_unavailable`, `transcription.license_scope` and `transcription.gated.muscriptor`.

### R3s SSH host (when "An SSH host")

- Host: an alias from `~/.ssh/config` or `user@host`. A port or another user belongs in a `~/.ssh/config` Host entry; the host key must already be in `known_hosts` (connections never accept new keys).
- Worker directory, relative to the remote home (default `piakura-worker`). Its parent must exist; an existing directory is used only if piakura created it.
- Ask for two separate permissions: a read-only check now (`piakura doctor --ssh HOST --root DIR`), and later, deploying the worker code there and downloading several GB of environments and models into that directory. The worker never uses sudo or changes system packages.

## R4 Arrangement

1. Levels: Easy, Medium, Hard (multi-select; default all three).
2. Keyboard: 88 keys / 61 / 49 / 25 / other.
3. Fewer than 88 keys: range mode (fixed range; or switch with octave shifts at rests), key policy (keep the original key; or transpose automatically) — multi-select, each choice becomes a version — and the lowest note (auto or a MIDI number) with the instrument's model name if known.
4. Piano layout (both hands on channel 1 = solo; left hand on channel 2 = split) and Easy's melody (keep every note / simplification allowed).

## R5 Review and output

1. Where to open the review page. It starts as soon as the job exists and runs on its own: it shows the stages and your notes as they happen, then the results to listen to and comment on, and keeps what the reviewer submits even while no agent runs. This machine (default; `local`) / inside the user's tailnet with `tailscale serve` (`tailscale-serve`) / through `ssh -L` from another computer (`ssh-tunnel`) / no review page (`none`). Saved as `review.access`.
   When `piakura doctor --review` reports tailscale logged in, suggest it: "Serving inside your tailnet with `tailscale serve` lets you open the review on a tablet too. Use it?" Always state:
   - This uses `tailscale serve`, not `tailscale funnel`: only devices in your own tailnet can reach it, not the internet. HTTPS also gives the review UI the secure context it needs for playback.
   - The review UI has no login of its own. Anyone your tailnet's access rules allow, including shared users and devices, can open it.
   - `piakura review stop` removes only the port piakura added (`tailscale serve --https=<port> off`). Do not use `tailscale serve reset`, which also removes other serve settings.
   Never offer funnel. If the user asks for it, explain that the unauthenticated UI and the recording would be public on the internet, and go ahead only after they confirm.
2. Only while `tools.link_bin` is unset: put the `piakura` command on your PATH? It links `~/.local/bin/piakura` (or `$XDG_BIN_HOME/piakura`) to the installed tools, so you can start and stop the review page yourself (`piakura review start`) without an agent. Nothing else changes; an existing file there is left alone, and if that directory is not on your PATH you are told how to add it. Yes / No. Save the answer right away with `$P config set tools.link_bin true|false --scope user`: it describes this computer, whatever R6 says.
3. Pace: run to the end / stop after each stage for a look.
4. Work and delivery directories (defaults `piakura/work/<slug>` and `piakura/dist/<slug>` under the current directory); inside a Git repository, whether to add them to `.gitignore` (recommended: copyrighted material stays out of commits).
5. Language of reports and the delivery README.

## R6 Confirm and save

Show one summary of all answers. Then ask where to keep the reusable answers:

- User settings (every project on this computer)
- This project's settings (`.piakura/config.json` at the project root)
- Do not save

Save with `piakura config set KEY VALUE --scope user|project`. Per-song answers (input, rights confirmation, title) are never saved as settings; they go to the job file.
