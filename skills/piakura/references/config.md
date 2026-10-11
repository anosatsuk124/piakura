# Settings

`piakura` keeps reusable answers in JSON files (`"format": "piakura-config/1"`):

- User: `${XDG_CONFIG_HOME:-~/.config}/piakura/config.json` (macOS too).
- Project: `.piakura/config.json` in the current directory or a parent up to the Git root.

Precedence, highest first: command-line flags, `PIAKURA_*` environment variables, project, user, defaults (for `language`, the locale before the default). A setting without a default stays unset until the user answers it. The consent record lives only in the user file. Secrets (Hugging Face tokens, API keys) are never stored here; Hugging Face uses its own login.

```bash
P="bash ../piakura-arranger/scripts/tool.sh piakura"   # from this skill's directory
$P config resolve --json            # every effective value and where it came from
$P config get arrangement.keys
$P config set arrangement.levels easy,medium --scope user
$P config unset transcription.device --scope project
$P config path                      # both file locations
$P config keys
```

| Key | Values | Default | Asked in |
|---|---|---|---|
| `tools.link_bin` | `true`, `false` (user settings only) | — | R5 |
| `language` | `en`, `ja` | the locale's (`LC_ALL`, `LC_MESSAGES`, `LANG`), else `en` | R5 |
| `checkpoints` | `end-to-end`, `each-stage` | `end-to-end` | R5 |
| `workspace.work_root` | directory | `piakura/work` | R5 |
| `workspace.delivery_root` | directory | `piakura/dist` | R5 |
| `workspace.gitignore` | `true`, `false` | `true` | R5 |
| `transcription.where` | `local`, `ssh` | — | R3 |
| `transcription.how` | `direct`, `container` | `direct` | R3 |
| `transcription.device` | `cuda`, `cpu` | — | R3 |
| `transcription.gpu_unavailable` | `wait`, `stop`, `cpu` | `stop` | R3 |
| `transcription.wait_minutes` | minutes | `60` | — |
| `transcription.license_scope` | `noncommercial`, `commercial` | — | R3 |
| `transcription.gated.muscriptor` | `true`, `false` | `false` | R3 |
| `transcription.paid_assist.provider` | `none`, `antigravity`, `openrouter` | `none` | only on request |
| `transcription.paid_assist.budget_usd` | number | `0` | only on request |
| `transcription.local.runtime_dir` | directory | `$XDG_CACHE_HOME/piakura/transcription` | — |
| `transcription.ssh.host` | ssh alias or `user@host` | — | R3s |
| `transcription.ssh.root` | directory under the remote home | `piakura-worker` | R3s |
| `transcription.ssh.state_file` | file | `$XDG_STATE_HOME/piakura/workers/<host>.json` | — |
| `transcription.container.image` | image reference | the release's worker image | — |
| `transcription.container.volume` | Docker volume | `piakura-worker` | — |
| `transcription.container.inference_network` | `none`, `default` | `none` | — |
| `arrangement.levels` | list of `easy`, `medium`, `hard` | all three | R4 |
| `arrangement.piano_mode` | `solo`, `split` | `solo` | R4 |
| `arrangement.keys` | number of keys | `88` | R4 |
| `arrangement.lowest_note` | `auto` or MIDI note | `auto` | R4 |
| `arrangement.range_modes` | list of `fixed`, `switch` | `fixed` | R4 |
| `arrangement.key_policies` | list of `preserve`, `auto-transpose` | `preserve` | R4 |
| `arrangement.easy_melody` | `exact`, `simplify` | `exact` | R4 |
| `arrangement.instrument` | model name | — | R4 |
| `review.access` | `none`, `local`, `tailscale-serve`, `ssh-tunnel` | `local` | R5 |
| `review.port` | port | — | — |
| `terms.accepted_version`, `terms.accepted_at` | set by `piakura terms accept` | — | R0 |

Environment variables override files: `PIAKURA_LANGUAGE` (`language`), `PIAKURA_TRANSCRIPTION_HOST` (`transcription.ssh.host`), `PIAKURA_WORKER_ROOT` (`transcription.ssh.root`), `PIAKURA_WORKER_STATE` (`transcription.ssh.state_file`), `PIAKURA_TRANSCRIPTION_RUNTIME` (`transcription.local.runtime_dir`), `PIAKURA_WORKER_IMAGE` (`transcription.container.image`). `PIAKURA_BIN` selects the tool directory and `PIAKURA_RELEASE_URL` the release download location (`scripts/install.sh`).

## Job file

`piakura job init` writes `$WORK/piakura-job.json` (`piakura-job/1`): the input (kind, absolute path or URL, SHA-256 of a file, title, artist, the time the user confirmed their rights), a snapshot of the resolved settings, the work and delivery directories, the `route` (the stages this input runs, in order; `review` last unless `review.access` is `none`), the stages recorded so far, a progress `log` and the piakura version.

- `piakura job stage "$WORK" NAME STATE [--output PATH]... [--note TEXT]` records a stage (`started`, `done`, `failed`, `skipped`) and logs it. Outputs inside `$WORK` are stored relative to it.
- `piakura job note "$WORK" TEXT [--stage NAME]` logs what you are doing, for the reviewer watching the page; write one before each long step.
- `piakura job show "$WORK"` prints the job.
- `piakura job next ["$WORK"] [--json]` says what a resumed run does first (`piakura-next/1`: `action`, `stage`, `reason`, `details`, `review_url`); see [workflow](workflow.md#resuming). Without `$WORK` it takes the current directory's job or the only one under the work root.
- `piakura job list [--root DIR]... [--json]` lists the jobs under the current directory and the work root (four levels deep), latest activity first, with each stage's state.

The log keeps the latest 200 entries. Updates take `$WORK/.piakura-job.lock`, so the agent, the review server and a person at the shell can record at the same time.

## Review page

The review page of a job runs on its own, with or without an agent; a person can start it from a shell.

- `piakura review start ["$WORK"] [--port N] [--share local|tailscale-serve|ssh-tunnel] [--https-port N] [--json]` starts `piakura-review serve` in the background (log in `$WORK/review/server.log`), or reports the server already running. It works before anything is published: the page shows the job's progress and the reviewer can submit. The job remembers the port, the share and the tailnet HTTPS port (default: the local port + 2), so the address stays the same next time. With `tailscale-serve` it adds `tailscale serve --https=PORT` (never funnel) unless that port already forwards to the page, and refuses a port that forwards elsewhere.
- `piakura review status ["$WORK"] [--json]` and `piakura review url ["$WORK"]` (exit 3 when not running).
- `piakura review stop ["$WORK"] [--end]` stops the server and removes only the tailnet port it added; `--end` also records the review stage as done.
