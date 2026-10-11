# Approximate transcription comparison

`midieval reference.mid candidate.mid --json` is a read-only command that approximately matches a transcription candidate against a reference MIDI. It is an evaluation separate from `mididiff`'s exact semantic equality and from `midistat`'s melody preservation contract, and it gives no PASS/FAIL on musicality.

`--reference-channels 1,2` and `--candidate-channels 3` are 1-based. Omitted means all channels; CH10 is excluded by default (`--include-drums` includes it). Other percussion banks and model-specific instrument classes are not excluded automatically, so check each channel's role before choosing channels. Program numbers and velocity are not match criteria. Ambiguous same-pitch pairs and non-positive durations make the evaluation refuse. Warnings from the source SMFs stay in the JSON.

It computes a maximum one-to-one matching from pitch and onset seconds (default ±0.05 seconds, set with `--onset-tolerance`). PPQN and tempo changes are converted to seconds per SMF. No reference note is matched to more than one candidate note. Metrics with durations also require the end-time difference to be within the larger of 20% of the reference note's duration and 50ms. This is an independent implementation following [the common MIR evaluation criteria](https://mir-eval.readthedocs.io/latest/api/transcription.html); it does not match mir_eval down to numeric rounding.

`pitch_onset` and `pitch_onset_offset` give precision, recall, F1 and the number of matched notes. `pitch_class_onset` is a diagnostic that ignores octaves; never substitute it for the main metrics. `sounding_pitch_class_jaccard` is the intersection/union of the sounding pitch-class sets, averaged with weights by the length of the sounding spans. It does not show correct harmonic function, and silence is not in the denominator. F1 with both sides empty, precision with an empty candidate and recall with an empty reference are null. Mean errors cover matched notes only.

## Time alignment across editions and performances

`--alignment alignment.json` gives linear interpolation within segments from candidate seconds to reference seconds. Each segment needs at least 2 anchors. Seconds are non-negative finite values; within each segment both timelines strictly increase, and segments keep their order on both timelines without overlapping. Mapping a repeat to a different occurrence is a separate comparison run.

```json
{
  "version": 1,
  "segments": [
    [
      {"reference_seconds": 12.0, "candidate_seconds": 0.0},
      {"reference_seconds": 24.0, "candidate_seconds": 12.1},
      {"reference_seconds": 36.0, "candidate_seconds": 24.0}
    ]
  ]
}
```

Confirm the shared segments and anchors from the audio, phrases and beats, and use the same ones for comparing every model. Keep the anchors fixed rather than adjusting them to maximize any candidate's note matches. There is no interpolation across segments and no extrapolation. Notes whose onset lies within a segment (start inclusive, end exclusive) are evaluated, and the number of notes outside is reported separately. A sustained note that started before a segment is not in this selection. A note running past the segment end is truncated in the harmony tally, not counted in matches with durations, and excluded from the mean duration error.

Without alignment, both files are taken to share one timeline in seconds. If the time correspondence is unknown, do not read the result as transcription accuracy. Input/argument errors exit 2; a successful evaluation exits 0 regardless of accuracy. `-o` writes atomically to a file that must differ from the inputs and the alignment.
