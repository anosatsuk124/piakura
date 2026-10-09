# Review source timing before arranging

For competing pitches, note-boundary scores, neural vocal models and optional
audio-model review, use [candidate evidence](candidate-evidence.md).

Use this workflow for audio-derived scores and for reports of wrong timing or
musically broken arrangements. Separate three questions: does the score match
the recording, does the piano arrangement carry the musical roles, and does it
meet the physical piano constraints? Compilation and preservation answer only
part of the last two questions.

## Establish a shared audio clock

The locked `audio` environment provides reproducible evidence commands:

```bash
bash scripts/transcribe.sh setup audio
bash scripts/transcribe.sh review beats "$WORK/audio.wav" "$WORK/beats.json" --model small0
bash scripts/transcribe.sh review pulse "$WORK/beats.json" "$WORK/pulse.json" --bpm 120
bash scripts/transcribe.sh review pitch "$WORK/vocals.wav" "$WORK/pitch.json" --start 12 --duration 10
bash scripts/transcribe.sh review agreement "$WORK/prepared/song.json" "$WORK/pitch.json" "$WORK/agreement.json" --channels 1
```

Use the recording's estimated BPM in `pulse`; 120 above is an example. Compare
`final0` if the first beat tracker misses a section. Save both predictions.
Inspect drums and repeated attacks when trackers choose half/double time or
disagree on downbeats. A low residual supports a pulse hypothesis, not a meter
or every accompaniment attack. Start with an offset-corrected constant clock;
use local tempo segments only when sustained residual drift supports them.

Commands write source hashes, source-file seconds, model identity and review
status. When the input itself is a cropped file, add its ingest offset to these
seconds exactly once. F0 probabilities describe voicing, not note correctness.
Check pitch slides, harmonics and separation bleed in the original mix. A short
stable F0 segment is not automatically a separately attacked score note.

Build the reproducible path from the supplied mixed recording, with separation
derived from that recording when needed. An official instrumental or isolated
stem can help diagnose bleed, but remains optional diagnostic evidence. Select
models and corrections on the mixed-recording path; verify the workflow again
with external stems unavailable. Similar F0 across independent source views can
rule against a separation-only explanation while leaving note segmentation,
voice selection and intended pitch unresolved.

`agreement` consumes the Go sidecar and reports absolute/octave-insensitive
voiced-frame agreement, coverage, support for simultaneous predicted notes and
a diagnostic 100 ms timing margin. Its
denominator is only high-voicing-probability frames; it does not detect every
missing note or prove onset accuracy. Inspect coverage and compare candidates
on the same evidence file. For a separately cropped source, `--source-offset`
maps the evidence's seconds to the sidecar's seconds; never fit it per candidate.

Record reviewed anchors as `{ "seconds": 1.25, "beat": 2.5 }` in the private
evidence. `audio_review.BeatClock` interpolates in both directions and refuses
extrapolation. Include the pickup and full score boundary. Preserve individual
voice timing through the map; changes to a singer's attacks need that voice's
own evidence, even when a drum pulse is clear.

For weak attacks, suspected missing notes, artificial rests or uneven instrumental timing, use [rhythm reconstruction](rhythm-reconstruction.md). Inspect each essential voice and its handoffs; a repaired vocal clock does not validate an inherited instrumental line.

## Compare a minimal musical reconstruction

Freeze excerpts spanning an exposed melody, dense singing, an instrumental lead
and a texture change. Keep evaluation phrases out of model/parameter selection;
group repeated motifs together. Preserve original models and the previous
delivery as separate candidates. First compare melody alone, then melody with
bass, then harmony and characteristic figures. Use the same piano renderer and
gain for candidates, with source audio aligned to the same seconds. Check tails
and renderer latency before interpreting an audible offset.

Freeze independently checked reference notes before scoring candidate changes
with `midieval`. Report reference coverage and ambiguous boundaries. Acoustic
agreement with another estimator is a diagnostic, not ground-truth F1. Record
raw timing error before any alignment; candidate-specific DTW can hide the bug.
If listening is requested, supply short source/previous/candidate audio and
capture the listener's timing, melody, harmony and phrasing judgments separately.
Unperformed listening remains unperformed in the report.

Confirm harmonic changes from the chordal source, bass and melody together.
A quiet or unresolved bass stem does not establish silence in the harmony.
Carry a stable voicing through its supported duration; decide rests from the
phrase, not from an empty analysis bin. Add inner voices only after melody and
bass form a coherent phrase. Difficulty changes texture and hand allocation;
Hard does not require a continuous generated arpeggio.

Change one stage at a time and retain before/after evidence. A learned correction
must beat a nonlearned baseline on held-out phrases without losing legitimate
short, syncopated, chromatic or repeated notes. Target-song labels and learned
target-specific exceptions stay outside an independent skill trial's bundle.
Evaluate transfer to the actual input texture separately: gains on clean solo
singing do not establish gains on a separated commercial mix. When the listener
rejects a candidate, retain that failure even if its benchmark improves; resolve
the disputed phrase before propagating its decoder across the song.
