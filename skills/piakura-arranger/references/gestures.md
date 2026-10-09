# Gestures and spurious ornamental notes

## Hear or inspect the musical action before counting notes

Classify a disputed rapid passage as an articulated melody/run, arpeggio, trill,
keyboard glissando, continuous instrument slide, or unresolved mixture. An AMT
decoder can turn one moving pitch into a chromatic staircase, count a decaying
partial as a new attack, or switch to another instrument mid-phrase. A dense
MIDI sequence alone does not establish many intentional piano keystrokes.

Compare the original mix, a derived stem and raw candidate alternatives on the
same clock. Look for renewed attacks, stable pitch plateaus, direction, register,
repetition and destination. A spectrogram can support a continuous contour but
cannot by itself prove articulation. An audio-capable model is an auxiliary
opinion: check its claimed interval against measured events and abstain when
its timing or source identification conflicts with the evidence.

## Decide whether the piano needs the gesture

Identify its musical role before choosing a piano technique. First mark
identity-bearing ornaments and structural holds using
[phrase design](phrase-design.md#protect-holds-and-defining-ornaments).
A recurring turn, appoggiatura, grace-note approach or run that defines the tune
belongs in the protected musical contract, even if it is short or difficult.
Reduce competing accompaniment before replacing such a gesture. Its length,
note density or instrument does not establish optionality. Preserve an instrumental
response in a vocal gap when it carries the phrase. If the requested difficulty
requires a replacement, compare its contour, rhythm and arrival with the original
gesture in context.

Record essential melody separately from optional fills before freezing the
retention reference. For an existing handoff, preserve its original artifacts
and document an authorized role/retention change in a new handoff. Never silently
drop required notes merely to make the validator pass. Identify a harmonic
replacement as an arrangement choice, not evidence that the source had no fill.

## Translate a retained action to piano

Record the gesture's start/end anchors, direction, range, rhythmic destination,
dynamic envelope and source uncertainty. Preserve those properties when adapting
the intermediate motion. A supported articulated scale keeps its essential
notes and rhythm. A continuous slide needs an explicit piano interpretation.
Choose a white-key glissando, suitable black-key glissando, written scalar run,
or reduced anchor figure according to the musical context and requested
difficulty. Label a changed pitch collection as an arrangement choice rather
than a recovered transcription. Do not convert every slide to a chromatic scale
or every descending run to white keys.

Shape one gesture: coherent short inter-onset intervals, intentional acceleration
only where useful, an audible approach/landing, and restrained intermediate
velocities. Uniform full-strength attacks and abrupt gaps can turn a sweep into
mechanical repeated hammering. Quantize its anchors or destination when warranted;
snapping each intermediate note independently can destroy the sweep. Reserve
hand space by simplifying accompaniment during the gesture. A glissando's high
note density is different from that many separately fingered melody attacks;
retain the validator warning and explain the intended technique.

## Remove clutter without erasing the tune

Prioritize removal of duplicate accompaniment, overtone voices, unsupported
one-off pitch flickers and fragments of one continuous gesture. A short note is
not automatically noise: preserve supported repeated syllables, pickups,
passing tones and syncopation. Use multiple cues for deletion, such as absent
renewed attacks plus unstable pitch/role and no independent or repeated-phrase
support. When source evidence is inconclusive and the user prioritizes a clean
piano arrangement, a simpler interpretation may be chosen explicitly; do not
claim that the omitted ornament was objectively absent from the recording.

Keep raw proposals and a before/after passage. Edit the authoritative MML with
`@gesture` or `@omission` comments containing the source interval and musical
reason. Update the selected reference only for the authorized changed passages;
preserve listener-accepted phrases and unaffected melody. Recompile, validate
the revised retention contract, and compare the passage alone and in context.
Technical PASS does not establish that the gesture sounds natural.
