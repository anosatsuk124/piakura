# Workflow

The sibling skills do the musical work; this file routes between them and records progress in the job. Read each sibling's SKILL.md when its stage starts and follow it completely. `$WORK` and `$DELIVERY` are the job's `paths.work` and `paths.delivery`; `P` is `bash ../piakura-arranger/scripts/tool.sh piakura`.

Record each stage when it starts (`$P job stage "$WORK" NAME started`) and when it ends: `done --output PATH…`, `failed` with a `--note` explaining why, or `skipped`. With `checkpoints: each-stage`, stop after recording and show the user the stage's results before continuing.

## Routes

The job's `route` holds its stages in order (`piakura job init` sets it):

| Input kind | Stages |
|---|---|
| `midi` (made by a person) | arrangement → delivery → review |
| `model-midi` | transcription (reconstruct from the MIDI, with the recording as evidence if supplied) → handoff → arrangement → delivery → review |
| `audio`, `url` | ingest → transcription (inference and reconstruction) → handoff → arrangement → delivery → review |

Review comes last and only when `review.access` is not `none`: the reviewer listens to what was delivered, and each answered round is delivered again.

## What the reviewer sees

The review page runs from the start and shows, by itself, the route with each stage's state, your stage records and notes, whether an agent is waiting for feedback, and the files that changed lately in `$WORK`. It needs nothing from you beyond the job records, but two habits make it useful:

- Before every step that takes minutes (download, environment setup, inference, a full arrangement pass), write `$P job note "$WORK" "what runs and about how long" --stage NAME`.
- Publish each stage's results as soon as they exist, so the reviewer can listen and comment early ([piakura-review](../../piakura-review/SKILL.md) for the spec):

| After | Publish |
|---|---|
| ingest | the recording only (`audio`, no layers) |
| transcription | the model candidates and the reconstruction so far |
| handoff | the reviewed reference (`role: transcription`) |
| arrangement | each level (`role: arrangement`) with its readable view |
| delivery | the delivered levels, then the review stage begins |

When feedback is pending that a revision does not answer, publish it with `--responds-to none`: the feedback stays pending, and publish refuses rather than mark it answered without a reply.

## ingest

```bash
bash ../piakura-transcription/scripts/transcribe.sh ingest 'URL-or-path' "$WORK/source"
```

A URL is downloaded with yt-dlp; local audio is converted the same way. The helper never reads browser cookies; if a download is refused, report it and ask for a local file.

## transcription

Follow [piakura-transcription](../../piakura-transcription/SKILL.md) from "Establish the recording and evidence". Choose backends by the job's `transcription.license_scope`:

- `noncommercial`: start with YourMT3 for a mixed song; add Basic Pitch for an isolated stem. SheetSage2, GAME, ROSVOT and MuScriptor (only with `gated.muscriptor: true`) are available as further evidence.
- `commercial`: do not use MuScriptor, SheetSage2, GAME or the becruily guitar model. Before using YourMT3, Demucs, ROSVOT/RMVPE, Beat This or torchcrepe, tell the user their weight licenses are conflicting or unverified (see [terms](terms.md)) and use them only if the user accepts; Basic Pitch is Apache-2.0.

Run inference where the job's settings say:

- `where: local`, `how: direct`: `bash ../piakura-transcription/scripts/transcribe.sh setup yourmt3`, then `… infer "$WORK/source/audio.wav" "$WORK/candidate-yourmt3" --model yourmt3 --device cuda|cpu`. The first setup downloads several GB into the runtime directory.
- `where: ssh`, `how: direct`: after the user allowed it in R3s, `bash ../piakura-transcription/scripts/worker.sh --host HOST deploy --root ROOT --backend yourmt3`, then `submit`, `status`, `fetch` as [GPU worker](../../piakura-transcription/references/gpu-worker.md) describes.
- `how: container`: the same commands with `--transport docker` (this machine) or `--transport ssh-docker --host HOST`, as the container section of [GPU worker](../../piakura-transcription/references/gpu-worker.md) describes. `deploy` uses the release's worker image (pulling it only when that Docker does not have it) and initializes its volume.

When the GPU is unavailable, follow `transcription.gpu_unavailable`: `wait` (retry for up to `wait_minutes`), `stop` (report and record the stage as failed), or `cpu` (only because the user allowed it).

## handoff

The transcription skill's handoff: `transcribe.sh handoff …` and `verify-handoff`. Record the handoff directory as the stage output; the arrangement uses its `reference_midi` and `melody_channels`.

## arrangement

Follow [piakura-arranger](../../piakura-arranger/SKILL.md) with the job's settings: `levels`, `keys`, `lowest_note`, `range_modes` × `key_policies` for fewer than 88 keys, `piano_mode`, and `easy_melody` (`simplify` is the user's authorization to reduce the Easy melody). It writes [readable MML](../../piakura-readable-mml/SKILL.md).

## delivery

`bash ../piakura-arranger/scripts/export.sh "$WORK" "$DELIVERY"` after every level passes validation, with the customer-facing `arrangement-report.md` in `$WORK`. Tell the user where the delivery README and MIDI files are, and the musical limitations that matter for playing. When `job next` says `redeliver`, validate the changed levels and export again.

## review

Only when `review.access` is not `none`. The page already runs (`$P review start "$WORK"`, which also makes it reachable as the user chose; never funnel). Publish the delivered levels, record `review started`, and follow [piakura-review](../../piakura-review/SKILL.md) from waiting for feedback: answer every submission with replies, publish, and deliver again (`redeliver`). When the reviewer ends the review, run `$P review stop "$WORK" --end`: it records the stage as done, stops the page and removes only the tailnet port piakura added.

You do not have to stay running while the reviewer listens. Unless the user is watching or `checkpoints` is `each-stage`, end your turn with the URL once everything is answered; the page keeps running, submissions are saved, and the next run (`job next`: `answer-feedback`) answers them first.

## Resuming

When a job exists, run `$P job next "$WORK"` and act on its `action`; run it again after each step. It checks the input's SHA-256, the recorded outputs of done stages and the review's unanswered submissions, so do not repeat those checks. Settings come from the job's snapshot unless the user asks to change them.

| `action` | What to do |
|---|---|
| `input-changed` | The input file changed or is gone. Tell the user; a changed input starts a new job in a new work directory. |
| `rerun-stage` | Outputs of a done stage are gone (`details`). Run that stage again; later stages that used them follow. |
| `answer-feedback` | The reviewer submitted feedback that no revision answers (`details` lists the files). Answer it as [piakura-review](../../piakura-review/SKILL.md) describes, even if an earlier stage is unfinished: say what you will do and when. |
| `redeliver` | A revision answered feedback after the last delivery. Validate and run the delivery stage again. |
| `run-stage` | Start `stage`. |
| `resume-stage` | `stage` started and did not finish. Look at what it left in `$WORK`, continue from there and record it. |
| `retry-stage` | `stage` failed (`reason` has the note). Fix the cause, or ask the user when it needs their decision. |
| `await-review` | Everything is answered; the review stays open. With `checkpoints: each-stage`, or when the user is watching, wait with `bash ../piakura-arranger/scripts/tool.sh piakura-review wait "$WORK/review/review.json"` in the background (it uses no tokens while waiting). Otherwise end the turn with the review URL: feedback submitted meanwhile is saved, and the next run answers it. |
| `complete` | Every stage is done or skipped. Report as in Finishing. |

## Finishing

Done when every requested level is delivered with PASS validation, or a failure is reported with its stage, cause and what remains. Never label a failed or unresolved stage as complete.
