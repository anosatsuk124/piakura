# Candidate evidence before committing to a note

Use when the melody remains wrong or several plausible pitches/boundaries compete.
Keep source-model scores, acoustic agreement, theory and listener judgments separate.
The recording supplies evidence; the agent authors the musical reconstruction in MML.

## Native scores and clocks

`transcription setup melody` installs locked ROSVOT/RMVPE/CREPE dependencies and
hash-verified public checkpoints. `review pitch ... --method rmvpe|crepe` produces
F0 JSON plus a native salience NPZ. Both expose uncalibrated voicing scores, not
the probability that a note is correct. pYIN remains the default method. CREPE
reports its effective 32–2006 Hz limits; a requested piano range does not expand
the model. Decode bounds are clamped before upstream converts them to array indices.

`infer ... --model rosvot` accepts excerpts up to 30 seconds and retains the
upstream predicted MIDI, note/boundary logits, softmax/sigmoid values and F0.
Use 8–12 second phrases with one second of context on each side. Record the
excerpt origin; preserve notes crossing a context boundary and choose ownership
by original onset. Review conflicting boundary interpretations before stitching.
ROSVOT uses RMVPE internally, so their agreement is not independent confirmation.
Its supplied pitch temperature is very small; sharp softmax values are not proof
of correctness. Its minimum-boundary-gap and F0 cleanup can lose short notes.

Basic Pitch retains `raw.activations.npz` and adds `raw.evidence.npz`, whose
explicit times include upstream's window correction. It contains `note`, `onset`,
`contour`, `pitches` and `contour_pitches`. Preserve these clocks; do not reconstruct
time from a nominal hop alone. Unknown confidence remains null, never velocity.

### Optional SheetSage2 lead-sheet proposals

```bash
bash scripts/transcribe.sh setup sheetsage2
bash scripts/transcribe.sh infer "$WORK/audio.wav" "$WORK/candidate-sheetsage2" --model sheetsage2 --device cpu
# For a previously authorized GPU host, use the worker with --model sheetsage2.
```

The [official model](https://huggingface.co/m-a-p/SheetSage2) accepts the normal
mixed recording. The adapter pins upstream code, adapter weights and the verified
MERT base; weights are CC-BY-NC-4.0. Setup locks a CUDA 12.6 build usable on CPU
or a compatible GPU. Inference uses FP32, including on RTX 20xx. Retain separate
vocal/instrumental melody MIDI, chord proposals, events, original-time playback,
ABC and token tensors under the attempt's `sheetsage2/` directory. Prepare raw
MIDI with the Go tools before editing. Treat role changes as hypotheses.

The upstream melody benchmark uses pitch classes without offsets; it does not
validate absolute register or note releases. Check octave alternatives against
reliable F0/acoustic evidence in the supplied mix or a stem derived from it,
phrase by phrase, before authoring MML. Neither a fixed octave shift nor the
model's implied key/chords supplies that evidence. Inspect speech-like voice,
portamento, repeated notes, missing instrumental leads and harmony separately.

Native tensor `scores` are **grammar-masked logits**, while `logits` are unmasked.
`token-evidence.json` gives the selected token and top five alternatives after
softmax over permitted tokens, conditional on the generated prefix. It retains
window origins and exact token positions, which are not audio frame indices.
Use `tokens.json`/`events.json` to interpret their musical context. These values
do not measure calibrated note correctness, and the model's own chord/melody
agreement is correlated evidence. All raw tensors remain available. Source-file
seconds and crop offsets obey the same rule as other candidates.

### Optional GAME singing proposals

```bash
bash scripts/transcribe.sh setup game
bash scripts/transcribe.sh review game "$WORK/vocals.wav" "$WORK/game.json" --language ja --start 12 --duration 10
```

Use a vocal stem derived from the supplied mix and inspect the same interval in
the original recording. This CPU adapter pins the official GAME 1.0.3 large
ONNX archive and locked dependencies. Weights are CC-BY-NC-SA-4.0; see the
[official release](https://github.com/openvpi/GAME/releases/tag/v1.0.3).
Inputs are at most 30 seconds. JSON retains voiced/unvoiced regions, fractional
pitch, a nearest-MIDI hint, source-file times, source/model hashes and seed.
It does not emit a score or choose the intended musical note.

The upstream output named `scores` is a fractional MIDI pitch, **not confidence**.
Observation outputs expose the native boundary sigmoid and Gaussian-blurred
pitch-bin sigmoid without changing graph nodes or weights. These values are
neither mutually exclusive categorical probabilities nor calibrated note
correctness. Preserve adjacent alternatives when a slide lies between notes.
Regions often extend across an unvoiced tail: their endpoints do not measure
piano key-down duration. Review releases and repeated attacks acoustically.

The same-basename NPZ keeps `times`/`boundary_score`, all eight boundary steps
and logits, plus `note_times`/`note_pitch_bins`/`note_pitch_scores`. The latter
are region-midpoint observations with half-semitone bins in MIDI 0..127,
not per-frame pitch estimates. Complete 0..128 native bins are retained in
`raw_note_pitch_bins`/`raw_note_pitch_scores`; `note_pitch_logits` uses that
complete axis. Declare pitch observations as `score_kind: "activation"`, with
the explicit note time/pitch keys, when building a phrase packet. Keep
`monophonic` unset: region-midpoint samples cannot establish continuous gaps.
Boundary observations use `event_type: "note_boundary"` and `score_kind:
"sigmoid"`. The normal source-offset rule below still applies.

Compare this optional model with other candidates on the same phrases. A
synthetic pitch/onset pass or better solo-singing benchmark does not establish
accuracy in the recording being arranged.

## Build phrase packets

Run `transcription review evidence manifest.json packet.json`. Paths in the
version-1 manifest are relative to its directory. A minimal manifest is:

```json
{
  "version": 1,
  "recording": {"path": "audio.wav", "duration_seconds": 20},
  "phrases": [{"id": "phrase-01", "start_seconds": 2, "end_seconds": 12}],
  "artifacts": [
    {"id": "raw-lead", "kind": "notes", "path": "prepared/song.json",
     "channels": [1], "role": "melody", "source_offset_seconds": 0},
    {"id": "vocal-f0", "kind": "frames", "format": "pitch-json",
     "path": "pitch.json", "score_kind": "salience", "monophonic": true,
     "review_threshold": 0.03, "source_offset_seconds": 0},
    {"id": "raw-note", "kind": "frames", "format": "npz",
     "path": "raw.evidence.npz", "matrix": "note", "score_kind": "activation",
     "source_offset_seconds": 0}
  ]
}
```

NPZ `times` and `pitches` keys can be overridden. Every matrix must have explicit
time and pitch axes. `source_offset_seconds` adds the ingest origin exactly once.
An explicit monophonic review threshold only identifies unexplained contours for
inspection; it never inserts/deletes notes. Missing/empty evidence has coverage
and null uncertainty, not an asserted absence of melody. All selected raw notes
survive; per-note top-three pitches summarize each model separately.

Boundary evidence uses `kind: "boundaries"`, `format: "json"` (arrays `times`,
`scores`) or `format: "npz"` (default keys `times`, `boundary_score`, overridable
with `times`/`scores`). Declare `event_type: "note_onset"` or `"note_boundary"`,
`score_kind: "activation"` or `"sigmoid"`, and an explicit `review_threshold`.
Packets expose local maxima and those within 120 ms of each candidate attack.
These are competing timing evidence, not snap targets or calibrated confidence.
End points without two neighboring frames are not asserted to be peaks.

## Phrase decisions and theory

Compare candidate-only, candidates plus native scores, and scores plus musical
context on the same frozen examples. Keep reference labels out of prompts.
For each edit record source IDs, before/after pitch and times, supporting evidence,
competing explanation and unresolved status. Recover gaps from audio before
inventing connective notes. Review repeated attacks separately from continuous
vibrato/portamento. Check backing voices and instrumental lead handoffs.

Theory hypotheses may accompany a phrase: alternate keys/modes, chord quality
and inversion, harmonic change times, phrase ending, motif/variation and voice
continuity. Each includes its supporting source intervals and uncertainty.
Use these to compare acoustically plausible choices. Recognize passing/neighbor
tones, suspensions, anticipations, borrowed chords and tonicizations; a supported
chromatic tone or leap survives a simpler tonal hypothesis. Independent evidence
must support a harmony before it is used to judge the melody, avoiding circular
"this chord implies this note, therefore the chord is correct" reasoning.

## Optional audio reviewer

`review assist job.json review.json --provider antigravity --model MODEL` invokes
a fresh native-audio review. A version-1 job contains `prompt`, a JSON `schema`,
and `audio: [{"label": "source", "path": "source.wav"}, ...]` (up to four files).
Read only the named media. With the verified Antigravity CLI, a bare @path did not
deliver audio; native file/audio-tool access did. The helper copies only named audio into a
new input directory because the CLI sandbox refuses media outside its working
directory. It retains provider responses, including unsuccessful ones. Test the
actual path with known audio and include abstention when media access fails.

For an explicitly authorized paid fallback, use `--provider openrouter --model
MODEL --ledger shared-budget.json --budget-usd LIMIT`. Authentication stays in
`OPENROUTER_API_KEY`. The fixed shared ledger reserves a conservative request
ceiling and retains unknown charges after failures. Never reset the ledger to
retry around the limit. Provider responses are auxiliary opinions, not edits.

First test known pitch errors, missing notes, repeated attacks, onset shifts and
correct chromatic/short controls. Reverse A/B order and include identical pairs.
Use an audio reviewer only where it improves held-out decisions; preserve raw
responses and costs. An eloquent explanation or self-reported confidence is not
an accuracy measurement. Numeric evidence can remain useful when audio review
does not help.
