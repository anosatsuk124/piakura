# Voicing and exception validation

`midistat --check-voicing` checks the hands' layout and simultaneous semitones. The skill's validate/compare always use this check and `--require-pass`. For standalone midistat it stays optional, as before. The same rules apply regardless of key count or solo/split.

- `hand_crossing`: a note pair in which an actually held LH note is higher than an RH note.
- `close_interval`: a pair, in the same hand or different hands, whose held intervals overlap and whose sounding pitches are exactly 1 semitone apart. A pitch-class difference alone does not count.

The overlap is `[max(start), min(end))`. Zero-length notes are excluded, and an end and a start on the same tick do not overlap. Melody notes entering in the middle of a long chord are checked too. Pedal resonance is not added to this held-key check; it is handled separately when checking the sound. The shared-key release rules of [piano-output.md](piano-output.md) still apply.

The JSON's `voicing` contains `score_sha256`, optional `reference_sha256`, `detected`, `accepted`, `unresolved` and `issues`. issues lists the first 200; the counts cover all. Each issue has rule/start_tick/end_tick and, for each of its 2 notes, ref (track/on_order), hand and pitch. An unaccepted pair is a hard violation and FAILs. When hand assignment is unknown, the status stays UNKNOWN as before.

## VoicingReview v1

Accept a crossing only for a concrete musical reason, such as a voice handoff or an intended dialogue. "To fit 25 keys" alone is not a reason. A semitone may be accepted only when it preserves the dissonance of a sounding 1-semitone interval that existed simultaneously in the original. Rework adjacent notes produced by octave-compressing a wide interval.

Pass it with `--voicing-review "$WORK/easy-review.json"`. Take the hashes below from actual `sha256sum` output and the note IDs from `smf2sakura --no-split-channels --report` of the compiled MIDI. Write each `reason` in the job's language (`language` in the `settings` of `piakura-job.json`).

```json
{
  "version": 1,
  "score_sha256": "<compiled MIDI SHA256>",
  "exceptions": [
    {
      "rule": "hand_crossing",
      "notes": [{"track":1,"on_order":12},{"track":2,"on_order":8}],
      "reason": "The left hand's answering melody passes to the upper voice while the right hand takes the sustained lower voice."
    }
  ]
}
```

`close_interval` also needs `reference_sha256` at the top level of the review and `source_notes` in the exception (track/on_order of the original's 2 notes). source_notes are in the same order as notes. The validator checks that their pitch classes match after correcting for the declared global transposition, that they also overlap at a sounding interval of 1 semitone in the original, and that the original's overlap, corrected for PPQN and switch rests, covers the entire output overlap.

Unknown fields, more than 16MiB, multiple JSON values, an unknown version, a hash mismatch, a pair that does not exist, names the same note twice or is duplicated, a rule that matches no detected issue, an empty reason and unsuitable source evidence are input errors (exit 2). They leave an existing report in place. After recompiling, update the exceptions' IDs and hashes and recheck the reasons. An invalid review passed directly to the analysis API accepts no exception either.

An exception applies only to its pair and rule; it does not exempt range, per-hand limits, shared keys or melody preservation. The structure of ArrangementPlan v1 is unchanged. The review is not a separate editable score.

The machine check does not prove the reason's musical validity, harmonic function, voice leading or the absence of pedal blur. Compare the corresponding passage of the original with the finished MIDI and confirm that only the intended exceptions remain. Completing the skill requires both this comparison and a validation PASS.
