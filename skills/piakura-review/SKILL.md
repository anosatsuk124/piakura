---
name: piakura-review
description: Publish transcription or piano-arrangement results as an interactive review session (piano roll, MML, source-audio A/B), wait for the reviewer's feedback and answer it with new revisions. Use when a human will listen to, compare or comment on transcriptions/arrangements, or when review feedback arrives.
---

# Piakura review

`piakura-review` serves one review session: every layer you publish on a piano roll with its MML, the source recording for A/B listening, your section split and cautions. The reviewer comments on ranges and notes, records which layer is better, edits a draft and submits; you answer with a new revision, which their screen offers to Sync and diff. Run it as `bash ../piakura-arranger/scripts/tool.sh piakura-review …` (script paths here are relative to this skill's directory).

Usually reached from another piakura skill inside a piakura job; when invoked on its own without one, start from [piakura](../piakura/SKILL.md) so the user's consent, settings and `$WORK` exist.

The session lives in a review directory beside the work it reviews, inside the piakura job's `$WORK` (e.g. `$WORK/review/`). You own `spec.json` only. `review.json`, `objects/`, `feedback/` and `state.json` are written by the tool and the reviewer's browser; read them, never edit them. File formats: [format](references/format.md).

## 1. Describe the session

Write `spec.json`. Paths are relative to the review directory. Layer IDs stay stable across revisions, because diffs and the reviewer's draft follow IDs. Its text (title, labels, notes, cautions, annotations, replies) is in the job's [language](../piakura/references/language.md); the page's own words follow each reviewer's browser.

- `audio`: the supplied recording.
- `layers`, grouped by run or stage (`group`), each with exactly one of `mml`, `midi`, `f0`:
  - every model's raw output as `candidate`; excerpt jobs carry `offset_seconds` so they sit on the recording clock;
  - the corrected transcription (`transcription`, with `melody_channels`) when the input was a mixed recording;
  - each arrangement level (`arrangement`);
  - F0 contours (`pitch.json`) when the evidence has them.
- `grid`: the measured beat clock (a beats file, or `bpm`/`origin_seconds`/`beats_per_bar`), with a `note` stating how it was estimated. Score `Tempo()` in this project is a seconds clock, not the meter. `origin_seconds` is the downbeat of bar 1: the roll's bar lines and every layer's readable view count bars from it, so fix it with [clock evidence](../piakura-readable-mml/references/clock-evidence.md).
- `readable`: publish adds a generated [readable](../piakura-readable-mml/SKILL.md) view to every notes layer; choose its `section_set`, its `language` (the job's), and `"chords": "both"` so its bar comments carry names and degrees for the export video. Mark layers whose MML already is readable with `"readable": {"disabled": true}`, and add a readable score the reviewer should hear as its own `mml` layer with the `offset_seconds` from its report.
- `section_sets`: your section split; each section's `note` says what happens musically and `cautions` says what the reviewer should check there.
- `annotations`: every unresolved or uncertain passage and every validator warning or voicing issue that has a time, with `severity` and the MML comment IDs it concerns in `tags`.
- `summary`: the state of the work in one paragraph, including what is provisional.

Done when `bash ../piakura-arranger/scripts/tool.sh piakura-review publish spec.json -m "…" --dry-run` succeeds, no score layer reports notes without MML lines and no readable view warns of a constant offset; explain any that remain in an annotation.

## 2. Publish and open

```bash
bash ../piakura-arranger/scripts/tool.sh piakura-review publish "$WORK/review/spec.json" -m "what to listen for first"
```

Inside a piakura job the page already runs: `bash ../piakura-arranger/scripts/tool.sh piakura review start "$WORK"` started it (or reports it, with its URL), reachable as the job chose, and keeps it at the same address across restarts. The reviewer's screen offers Sync for each revision you publish. Publish work in progress with `--responds-to none` while feedback waits that it does not answer (step 5).

Outside a job, serve the review yourself and keep it running across revisions:

```bash
bash ../piakura-arranger/scripts/tool.sh piakura-review serve "$WORK/review/review.json"   # background; prints the URL
bash ../piakura-arranger/scripts/tool.sh piakura-review status "$WORK/review/review.json"  # URL, unanswered feedback
bash ../piakura-arranger/scripts/tool.sh piakura-review stop "$WORK/review/review.json"
```

`serve` works before the first publish (the page waits for it) and refuses to start twice on one review (exit 4, printing the running URL). Playback needs a secure context. Keep the default loopback `--addr`: open it on this machine, forward it with `ssh -L`, or, inside the user's tailnet, `tailscale serve --bg --https=PORT http://127.0.0.1:SERVER_PORT` (HTTPS for every device in the tailnet). Never use `tailscale funnel`: the UI has no login, and funnel would put it and the recording on the internet. Stop only that port afterwards with `tailscale serve --https=PORT off`, not `tailscale serve reset`. Tablets switch to a touch layout by themselves; `?ui=tablet` or `?ui=desktop` forces one. The tablet layout keeps its own view in `state-tablet.json`; the draft is shared.

## 3. Wait for feedback

Run `bash ../piakura-arranger/scripts/tool.sh piakura-review wait "$WORK/review/review.json"` as a background command. It exits when feedback is pending and prints each `feedback/NNNN.json` path; its exit is your notification. Exit 3 means `--timeout` passed without feedback. While it waits, the reviewer's page shows that an agent is waiting (`agent.json`); waiting costs no tokens.

You need not wait at all: the reviewer can submit while no agent runs, and the submissions stay pending until a revision answers them. In a piakura job, `piakura job next` returns `answer-feedback` for them the next time the job runs.

## 4. Answer every item

Read each pending feedback file in full. Treat the reviewer's input as musical evidence and proposals:

- **Range and note comments**: re-examine the passage against the audio and your evidence; `notes` cite the published notes with MML line and text. When a comment has `parts`, the reviewer was looking at only those tracks of the layer (e.g. the right hand), so the remark concerns them.
- **Preference comments** (`target: preference`): the reviewer heard `preferred` as better than `over` within `start`–`end`. Rebuild that passage from the preferred source with the owning skill's evidence rules, rather than copying notes wholesale.
- **Replies** (`target: reply`): the reviewer answers your earlier reply to the item `reply_to` names. Read that thread (the item, your reply in the revision's `replies`) and reconsider with fresh evidence.
- **Edits**: `ops` add, delete or modify notes; `before` cites the published note with its MML line (and `readable_line`, its bar in the readable view), `after` gives the new values with ticks on that layer's clock, and `from` names the layer an adopted note came from. `draft_midi`, `draft_mml` and `draft_readable` hold the reviewer's whole draft; `mml_text` is MML they typed. Apply edits to your MML at the cited lines, keeping its comments and structure.

Then rerun the owning skill's compile and validation ([piakura-transcription](../piakura-transcription/SKILL.md) handoff, [piakura-arranger](../piakura-arranger/SKILL.md) compile/validate) and update its evidence or report.

Done when `spec.json` `replies` holds `{"status": …, "text": …}` for every comment (replies included), keyed `<feedback id>/<comment id>`; for the summary when there is one, keyed `<feedback id>/summary`; and for every edited layer, keyed `<feedback id>/edit:<layer>`. The reviewer's comments tab shows each status as a mark beside your text:

- `fixed`: changed as asked; the text says what changed.
- `partial`: changed in part; the text says what and why not the rest.
- `kept`: kept the original against the comment; the text gives the evidence (the recording, the source, the difficulty limits).
- `answered`: nothing to change (a question, a remark); the text answers it.

## 5. Publish the answer

```bash
bash ../piakura-arranger/scripts/tool.sh piakura-review publish "$WORK/review/spec.json" -m "summary of the changes"
```

Publishing moves `replies` into the revision and marks the pending feedback answered (`--responds-to 0003,0004` narrows that). It refuses while a pending submission has a comment, summary or edit but no reply; `missing_replies` in its output lists what `--responds-to` answered without one. To show work in progress while feedback waits, publish with `--responds-to none`: the feedback stays pending. The reviewer's screen shows Sync, which diffs each changed layer against the previous revision. Return to step 3 until the reviewer ends the review, then stop the server.
