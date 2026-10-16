# Review session file formats

JSON keys are snake_case. Times are seconds of the source recording; `channel` is 1-based.

## spec.json (you write)

```json
{
  "format": "piakura-review-spec/1",
  "title": "Song — review",
  "summary": "Mixed-recording transcription and three levels; the bridge harmony is provisional.",
  "audio": [{ "id": "mix", "label": "Source (mix)", "path": "../source/audio.wav" }],
  "grid": { "bpm": 150.0067, "origin_seconds": 0.0207, "beats_per_bar": 4, "note": "pulse from drum attacks; meter provisional" },
  "readable": { "section_set": "main", "chords": "both", "language": "en" },
  "section_sets": [
    { "id": "main", "label": "Sections", "sections": [
      { "id": "verse-a", "label": "verse A", "start": 20.4, "end": 33.2,
        "note": "Lead enters over a sustained bass.", "cautions": ["Weak attack at 27.6 s"] }
    ] }
  ],
  "annotations": [
    { "id": "u001", "start": 12.99, "end": 13.21, "layers": ["transcription"],
      "tags": ["L0030"], "severity": "unresolved", "text": "Octave of the lead unresolved" }
  ],
  "layers": [
    { "id": "yourmt3", "group": "Models", "label": "YourMT3", "role": "candidate", "midi": "../raw/raw.mid" },
    { "id": "window-03", "group": "Models", "label": "SheetSage2 44–60 s", "role": "candidate",
      "midi": "../windows/03/raw.mid", "offset_seconds": 40 },
    { "id": "rmvpe", "group": "Models", "label": "Vocal F0", "role": "candidate", "f0": "../f0/pitch.json" },
    { "id": "transcription", "group": "Agent", "label": "Corrected", "role": "transcription",
      "mml": "../transcription.mml", "melody_channels": [1] },
    { "id": "easy", "group": "Agent", "label": "Easy", "role": "arrangement", "mml": "../easy.mml",
      "readable": { "disabled": true } },
    { "id": "transcription.readable", "group": "Agent", "label": "Corrected (readable)", "role": "transcription",
      "mml": "../transcription.readable.mml", "offset_seconds": -0.3793, "melody_channels": [1],
      "readable": { "disabled": true } }
  ],
  "replies": { "0001/c2": { "status": "fixed", "text": "Moved the A4 back to the downbeat; the recording supports it." } }
}
```

- `grid`: `beats` (a JSON file with `beats` and optional `downbeats` arrays, as Beat This writes) or `bpm` with `origin_seconds` and `beats_per_bar`. `origin_seconds` is a bar line (bar 1).
- `readable`: the generated readable view of every notes layer. `section_set` (default the first), `chords` (`names`, `roman`, `both` or `none`; default `names`), `clock` (`grid` when the grid has a `bpm`, else `score`), `language` (of the comment prose, the job's `language`; default `en`), `disabled`. A layer's `readable` overrides `section_set` or sets `disabled`, for MML that already is readable. A readable score added as a layer takes `offset_seconds` from its report: the recording second of its tick 0, negative when bar 0 starts before the recording.
- `severity`: `info`, `caution` or `unresolved`.
- `tags`: IDs that appear in MML comments (`// L0030 …`); the UI matches them in the comment text.
- `f0`: `times` and `pitch` (fractional MIDI note numbers, `null` when unvoiced), optional `voicing_score`.
- `replies`: answers for the next revision, `{status, text}` per feedback item (statuses in [step 4](../SKILL.md#4-answer-every-item)); publish rejects any other status, moves them into `review.json` and clears them here. Older revisions hold plain-string replies, which read as a reply without a status.

## feedback/NNNN.json (the reviewer submits)

```json
{
  "format": "piakura-review-feedback/1",
  "id": "0001",
  "submitted_at": "2026-10-08T04:05:22Z",
  "summary": "Overall the left hand is too choppy.",
  "comments": [
    { "id": "c1", "revision": "r1", "target": "preference", "start": 12.3, "end": 15.8,
      "layers": ["yourmt3", "transcription"], "preferred": "yourmt3", "over": ["transcription"],
      "text": "Here YourMT3 is better than the corrected transcription." },
    { "id": "c2", "revision": "r1", "target": "notes", "start": 1.12, "end": 1.9, "layers": ["easy"],
      "notes": [ NoteRef ], "text": "Octave too high?" },
    { "id": "c3", "revision": "r1", "target": "range", "start": 20.4, "end": 26.8, "layers": ["easy"],
      "parts": [ { "layer": "easy", "track": 1, "channel": 1, "label": "Right hand" } ],
      "text": "The melody loses the vocal rhythm here." }
  ],
  "edits": [
    { "layer": "easy", "revision": "r1", "draft_midi": "0001-easy.mid", "draft_mml": "0001-easy.mml",
      "draft_readable": "0001-easy.readable.mml",
      "ops": [
        { "op": "modify", "before": NoteRef, "after": NoteValue },
        { "op": "delete", "before": NoteRef },
        { "op": "add", "after": NoteValue, "from": { "layer": "yourmt3", "note": NoteRef } }
      ] }
  ]
}
```

- `target`: `range` (a time range across `layers`), `notes` (the cited notes), `preference` or `reply`.
- `reply_to` (replies only): the item of an earlier submission whose thread the reviewer answers, keyed like `replies` (`0001/c3`, `0001/summary`, `0001/edit:easy`). `start`, `end`, `layers` and `parts` repeat that item's.
- `parts` (range and preference comments, optional): for each layer listed, the comment concerns only the parts named, because the reviewer had hidden the others or drew the range on the score view over only these parts' staves (a part is the layer's notes on one `track`/`channel`; `label` is its TrackName, e.g. "Right hand", or `CH n` for MIDI layers). Layers in `layers` but not in `parts` are concerned whole.
- Every comment and edit carries the `revision` it was made on.
- `draft_midi` / `draft_mml` sit beside the JSON: the reviewer's complete draft for that layer, on the layer's own tick clock, with its tempo map and program/CC events. `draft_readable` is the same draft written like the layer's readable view (quantized; `draft_midi` keeps the exact notes). `mml_text` appears when the reviewer edited the MML text directly, or edited on the score view: then it is the layer's readable MML with the edited bars rewritten one bar per line (comments and other lines kept). With empty `ops` it is a text-only edit, such as the score view's Tidy, which rewrites the whole text with every sound kept.

NoteRef cites a published note:

```json
{ "track": 1, "on_order": 6, "channel": 1, "pitch": 81, "name": "o6a", "velocity": 43,
  "start_tick": 2688, "end_tick": 4560, "start": 1.12, "end": 1.9,
  "line": 13, "line_text": "Time(2688) o6 v43 q100 a%1872",
  "readable_line": 41, "readable_line_text": "/** @chord G:maj7 roman=IVM7 */ o6 l8 a2^8 r8 g f+ // 1" }
```

`track`/`on_order` is the same pair as `NoteRef` in arrangement plans and voicing reviews (compiled SMF track and NoteOn event index). `line` is the 1-based MML line that produced the note, `null` when unmapped; `line_text` is that line, so the note stays findable after you renumber; a note the reviewer added in the draft has `line: null` and `line_text: "(note added in draft)"`, whatever the page's language. `readable_line` / `readable_line_text` give the bar line of the layer's readable view when it has one; edit the MML that `line` cites.

NoteValue is a proposed note: `track`, `channel`, `pitch`, `name`, `velocity`, `start`, `end`, plus `start_tick`/`end_tick` on the layer's clock.

## What the tool writes

- `review.json`: `revisions[]`, each with `id` (`r1`, `r2`, …), `message`, `responds_to`, `replies` and the published `layers` pointing at content-addressed `objects/`. Lists are always arrays, possibly empty. Until the first publish there is no `review.json`; `serve`, `wait` and the reviewer's submissions work in the review directory all the same, with no revisions.
- `objects/<sha256>.json|mml|mid`: computed layers and copies of their sources; unchanged layers share objects across revisions.
- `server.json`: the running server (`url`, `pid`, `boot`), present only while `serve` runs. A second `serve` on the same review prints that URL and exits 4. `piakura-review status review.json [--json]` reports it with the revision count and the unanswered submissions (`piakura-review-status/1`); `piakura-review stop review.json` ends it.
- `agent.json`: present while `piakura-review wait` runs, with a heartbeat every 5 seconds; the reviewer's page shows that an agent is waiting and treats a record silent for 15 seconds as gone.
- The page also shows the job's progress: the stages and notes of `piakura-job.json` beside the review directory (`serve --job PATH` names another) and the files that changed lately in the work directory, two levels deep, outside `review/`.
- `state.json`: the reviewer's view, unsent draft and navigation markers (`markers`, not feedback).
- `state-tablet.json`: the view of the reviewer's tablet layout (`{format: "piakura-review-view/1", view}`). The draft and markers in `state.json` are shared by both layouts.

The reviewer's volumes and default settings live outside the review directory (`piakura-review/settings.json` in the user configuration directory, `~/.config` on Linux and `~/Library/Application Support` on macOS, and `piakura-review/mixers/` in the state directory, `~/.local/state` by default; each with a `-tablet` twin); you never need to read them.

## Line mapping limits

Notes map to the top-level MML statement that ran them. Inside a multi-line block (function, tuplet group spanning lines) they take the block's first line; a tie that spans lines takes the line where it closes. One note or chord per line, as in pretty output and `Time(…)`-per-note scores, maps exactly; in a readable score every note maps to its bar's line, including notes in `Sub{}`, `{}` and one-line loops.
