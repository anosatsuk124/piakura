# Confirmed piano validation specification

`midistat` analyzes held-key intervals and onsets on an 88-key piano (MIDI 21–108) by default, or over the range set by `--keys N --lowest-note MIDI` or an [arrangement plan](keyboard-arrangement.md). Sustain-pedal resonance does not count as finger occupancy. When an end and a start fall on the same tick, the end is processed first.

## Hand assignment and status

`--hands RH=1,LH=2` names track numbers (0-based) of the compiled SMF. Several tracks: `RH=1+3,LH=2`. PASS is possible only when every note's hand is determined. Without `--hands`, notes at MIDI 60 and above count as RH and those below as LH; the values computed this way are for reference only and the status is UNKNOWN. Notes not assigned to a hand, ambiguous same-pitch overlaps, unterminated notes and the like also make the status UNKNOWN.

|profile|simultaneous keys/hand|span of simultaneous keys|leap within 250ms|note count relative to the original (guideline)|
|---|---:|---:|---:|---|
|easy|3|12 semitones|at most 12 semitones|25–45%|
|medium|4|14 semitones|warning|45–70%|
|hard|5|warning (over 14 semitones)|warning|70–90%|

A leap is the larger of the moves between the lowest notes and between the highest notes of consecutive onset groups. The time between them integrates tempo changes. Count, span and leap violations record the tick and the hand. Meeting the hard constraints in the table does not guarantee playability, which also depends on actual fingering, hand size and practice. The difficulty thresholds are initial design values, not yet calibrated against real performance.

Easy's maximum 1-second note density of RH 4 notes / LH 2 notes and its LH onset interval of 2 beats are warning guidelines. The profile JSON's `max_rh_notes_per_second`, `max_lh_notes_per_second` and `min_lh_onset_beats` are likewise warning thresholds. Density counts every chord tone, so making these values hard constraints would lose the harmony. Prioritize the lead melody's pitch, rhythm and note values; reduce accompaniment doublings, inner voices and added fills. The LH uses 2 notes as the base and 3 where needed, combining the root with a 3rd/7th or similar to keep the harmony's character. Hold accompaniment notes until the next onset, harmony change or phrase end. An offbeat, a repeated note or a short gate alone does not make a note an ornament.

## Reference metrics

Records mean/max 1-second note density, max simultaneous keys, max span, max fast leap, repeated notes, the rate of onsets off the 16th-note grid, the rate of chord onsets, and simultaneous octave pairs. Span is the highest minus the lowest of all keys held by one hand. Density, repeated notes and rhythm are material for warnings and are not converted into an uncalibrated overall score.

## Comparison with the original

In `--reference original.mid --melody-channels 1`, the channels are the original's 1-based MIDI channels. Melody preservation matches the pitches and onset ticks of those channels in quarter-note units. It ignores tempo, so it warns when the reference and the score differ in tempo map or time signature. Compare an arrangement written in readable form with a readable reference quantized to the same clock (this skill's `scripts/readable-reference.sh`). Transposition and octave shifts do not count as matches. Without an arrangement plan, medium/hard require exact 100% preservation. With a plan, a preservation rate corrected for the declared global transposition, octave shifts and added rests is computed separately, and medium/hard require 100% after correction. The exact rate is kept too. For easy the preservation rate is reported only. Without these flags, melody preservation is unknown.

`--preserve-melody` makes the reference and the melody channels mandatory and requires every note's pitch, onset and held duration. A missing note FAILs as `melody_missing`; a changed held duration of a kept note FAILs as `melody_duration_changed`. The skill's validate/compare with a reference use this contract by default. An omission reason written in the plan does not exempt a note. When the user has approved simplifying the melody, follow [the skill's procedure](rhythm-and-articulation.md) and build a preservation contract, separate from the original transcription, that declares the changed range and the replacement notes. Report the exact validation against that contract together with the diff from the original reference, and never describe the result as 100% preservation of the original melody. Leave the validator's verdicts unchanged. Without `--preserve-melody`, the earlier verdicts above still apply.

`melody_duration_matched` and `melody_duration_preservation` are the count/rate of notes whose pitch, onset and held duration all match. With a plan, `adjusted_melody_duration_matched` and `adjusted_melody_duration_preservation` are output too. Held durations are compared as integer products, each multiplied by the other file's PPQN, without adding switch rests. The same rule applies to a note that ends exactly at a section end. Velocity is not part of this flag's check.

The note-count ratio uses the original's pitched notes as the denominator. Percussion is classified, for reference, as CH10 or as bank MSB 126/127 at NoteOn (a GM/XG heuristic). Device-specific bank assignments are not interpreted. Harmonic coverage is the recall of the onset pitch-class sets per quarter note; rhythm similarity is the recall of the set of pitched onset times. Neither measures the correctness of chord function or voice leading.

The JSON contains profile, status (PASS/FAIL/UNKNOWN), unknown_reasons, hard_violation_count, violations, warnings, metrics overall and per hand, and optional preservation. Violation details list the first 200; the total count is never truncated. FAIL takes precedence; with no hard violation, any unknown condition gives UNKNOWN. Exit 0 is PASS or UNKNOWN from a reference analysis, exit 1 is FAIL, exit 2 is a usage/input error. The skill checks status, not only the exit code.

With `--require-pass`, UNKNOWN also exits 1. The skill's validate helper passes this flag.

The skill's validate/compare also make `--check-voicing` mandatory. It detects hand crossings and sounding 1-semitone intervals during held intervals, and allows only exceptions tied to a specific note pair and to source evidence in the original. For its verdicts, JSON and exception contract see [voicing](voicing-contract.md). A standalone midistat analysis runs this check only when it is given explicitly, as before.
