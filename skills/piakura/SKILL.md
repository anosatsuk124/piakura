---
name: piakura
description: Entry point for piakura. Use when the user invokes $piakura or /piakura to turn a MIDI file, an audio file or an audio URL into Easy/Medium/Hard solo-piano arrangements. Asks every setup question up front, saves the answers if the user wants, then runs transcription, readable MML, arrangement, optional human review and delivery, and resumes an interrupted job.
disable-model-invocation: true
argument-hint: "[midi-or-audio-path-or-url]"
---

# piakura

You run the user's whole request from one invocation: consent, setup questions, tools, then the sibling skills [piakura-transcription](../piakura-transcription/SKILL.md), [piakura-readable-mml](../piakura-readable-mml/SKILL.md), [piakura-arranger](../piakura-arranger/SKILL.md) and [piakura-review](../piakura-review/SKILL.md). Musical decisions follow those skills; this one decides nothing musical.

Conventions: script paths are relative to this skill's directory; run them through its absolute path. After installation, `P` stands for `bash ../piakura-arranger/scripts/tool.sh piakura`. Talk to the user in their language. Never answer a question for them, accept a model's or a site's conditions for them, or send their audio, scores or settings to a service they did not choose.

## 1. Resume or start

When `bash scripts/install.sh --check` succeeds, run `$P job list` now; otherwise the tools are not installed yet, and you do this right after step 3. If the invocation names a work directory, or jobs exist, show them (title, stages, last update) and ask whether to resume one or start a new song. To resume:

1. `$P review start "$WORK"` unless the job's `review.access` is `none`. It reports the page if it already runs, and starts it otherwise; give the user the URL.
2. `$P job next "$WORK"` and continue at step 6 with that job's settings ([workflow](references/workflow.md#resuming)). Feedback the reviewer submitted while no agent ran comes first.

## 2. Consent

Read [terms](references/terms.md). Unless `$P terms status --version <TERMS_VERSION>` succeeds, ask round R0 of [intake](references/intake.md). Stop if the user declines.

## 3. Tools

Run `bash scripts/install.sh --terms-version <TERMS_VERSION>`, adding `--link-bin` when `tools.link_bin` is `true` in the user's settings; it prints the tool directory and changes nothing outside piakura's data directory except that link. A private release needs the GitHub CLI logged in; relay the script's message if it fails. Then record consent: `$P terms accept --version <TERMS_VERSION>`.

## 4. Questions

Follow [intake](references/intake.md): R1 saved settings (`$P config resolve --json`), then R2 input, R3 transcription (with R3s for an SSH host), R4 arrangement and R5 review and output. Run `$P doctor` with the flags the answers need (`--transcription`, `--ssh HOST --root DIR` after the user allowed the read-only check, `--review`) and resolve every required failure with the user before running anything long. [environment](references/environment.md) lists what each choice needs.

## 5. Confirm, save and create the job

Show one summary and ask R6. Save the reusable answers with `$P config set KEY VALUE --scope user|project` ([settings](references/config.md)). If the user just chose the PATH link in R5, run `bash scripts/install.sh --terms-version <TERMS_VERSION> --link-bin` and relay its messages. Pick a short slug from the title or file name; then:

```bash
WORK=<work_root>/<slug>; DELIVERY=<delivery_root>/<slug>
$P job init "$WORK" --kind midi|model-midi|audio|url --input PATH | --url URL \
  --delivery "$DELIVERY" --rights-confirmed [--title T] [--artist A] [--audio PATH]
```

Pass `--rights-confirmed` only after the user said yes in R2. Inside a Git repository, add the work and delivery roots to `.gitignore` if the user agreed.

Unless `review.access` is `none`, start the review page now, before any long step: `$P review start "$WORK"`. It runs on its own, so the user can watch the stages and your notes arrive, and comment as soon as you publish anything. Give them the URL it prints (the tailnet URL for `tailscale-serve`, with the caveats in [intake](references/intake.md) R5; for `ssh-tunnel`, its `ssh -L` hint).

## 6. Run

Repeat: `$P job next "$WORK"`, do what its `action` says ([workflow](references/workflow.md)), record the stage with `$P job stage`. The route runs ingest, transcription and handoff when the input needs them, then arrangement, delivery and review. Before each long step write a `$P job note`, and publish each stage's results for the reviewer as workflow describes; the page shows both without your involvement. Keep the user informed at each stage boundary; with `checkpoints: each-stage`, wait for them there.

## 7. Finish

Report the delivery directory, the files to play, PASS/FAIL for each level and the musical limitations that matter for playing. Name anything left unfinished and how to resume (`$piakura` again in the same project).

If the reviewer is still reviewing, leave the page running: their submissions are saved, and the next `$piakura` answers them first. Tell the user how to stop it (`piakura review stop "$WORK"`, adding `--end` when the review is over) and how to start it again later without an agent (`piakura review start "$WORK"`; the bare `piakura` command exists only if they chose the PATH link, otherwise give the full path from `$P paths`). When the reviewer has ended the review, run `$P review stop "$WORK" --end`; it removes only the `tailscale serve` port piakura added.
