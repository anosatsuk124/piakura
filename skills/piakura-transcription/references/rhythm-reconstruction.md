# Reconstruct rhythm, including weak and missing attacks

Model notes are proposals about a performance. Separate the intended rhythmic
position, the start of audible excitation, the later amplitude/F0 peak, and the
piano key-down duration. A soft attack, swell, consonant, slide or masked note
can cross a model threshold late or escape detection. Conversely, vibrato and
decay can produce extra notes. A sequence of confident pitches does not settle
its rhythm, articulation or completeness.

## Build competing phrase interpretations

Establish the pulse from several source attacks and repeated phrases. Test
straight, triplet, swung and syncopated subdivisions where relevant. Then write
the phrase's plausible note/rest pattern before choosing individual timestamps.
Include pickups, ties, repeated notes and genuine rests. Compare the raw model
pattern with that rhythmic hypothesis; investigate omitted weak beats and
uneven durations rather than preserving every model event by default.

For same-pitch repetitions or a phrase that seems to hesitate, record the whole
group's beat span as well as its attack count. Compare straight, dotted,
triplet/other tuplet and swung patterns, including the pickup and following
arrival. A locally stretched model interval may introduce accidental slowing;
an actual tuplet must survive reconstruction. Six attacks alone do not identify
a sextuplet. Use the [MML grouping and articulation reference](../../piakura-arranger/references/rhythm-and-articulation.md)
to express and compile-check the chosen pattern. Treat unsupported internal
boundaries as unresolved, even if every frame has the correct pitch class.

Use melody contour, interval patterns, motif repetitions, voice leading and
harmonic rhythm to propose missing notes or alternative boundaries. A repeated
motif is a comparison, not a copy template: check for deliberate variation.
Harmonic expectation can narrow a pitch choice, but cannot establish an attack
or require a chord tone at every slot. A gap in a MIDI line is not proof of a
rest, and a filled rhythmic grid is not proof of completeness.

## Test the proposed attack in the source

For a disputed note, inspect the original mix and a stem derived from it around
both the model time and the proposed musical time. Look backward from a strong
peak for the beginning of that pitch's excitation, not just the first loud or
high-confidence frame. Compare pitch-band energy and onset/boundary candidates
with neighboring harmonics and other voices: a drum transient or the previous
note's decay can create a misleading peak. Consult the [candidate evidence
commands](candidate-evidence.md) for native scores and competing boundaries.

Repeated notes need evidence of renewed excitation even when pitch is constant;
F0 alone cannot recover them. For a suspected omitted note, inspect the raw
activation/contour below the decoding threshold and compare a repeated phrase
or independent candidate. Retain an unresolved alternative if neither the
attack nor pitch is supported. If a useful piano connective note is composed
despite unresolved source evidence, label it as arrangement rather than recovered
transcription.

Inspect onset and sustained-frame scores separately. A decoder can show an
attack peak yet emit no note because the sustained activation or minimum-length
rule fails. Conversely, a sustained band can remain after the played note ends.
For Basic Pitch, compare `onset` and `note` in `raw.evidence.npz` on its supplied
time axis; do not infer absence from `raw.mid` alone. Lowering every threshold
can add accompaniment bleed and false reattacks. Use the phrase hypothesis and
original audio to review particular missing candidates instead.

Review releases independently. A decoder may cut a sustained note early or
bridge a real rest. Use the next attack, articulation and harmonic change to
reconstruct useful piano duration; a universal gate or a blanket legato rule
can manufacture gaps or erase phrasing. Preserve validated deliberate timing.

## Choose and verify the rhythm

When the source and phrase structure support regular timing, write the reviewed
note/rest pattern in musical values on the established clock. Record deliberate
displacements and exceptions. Quantization is a reconstruction decision in MML,
not a change to MIDI conversion or permission to round every voice. Inspect
instrumental handoffs as carefully as singing: an unchanged line from another
model can retain timing errors after the vocal line has been repaired.

For each changed passage, retain raw and revised MIDI plus source-time evidence
for moved, added, merged or lengthened notes. Report signed onset differences,
inter-onset intervals and unexpected gaps against the reviewed source anchors;
grid distance alone is not an accuracy measurement. Compare held-out repetitions
and preserve supported short, repeated, chromatic and syncopated counterexamples.

If multiple piano difficulty levels share a hesitation, inspect the common
reference before reducing Easy's note count. Repair a supported transcription
error once and regenerate its handoff for all affected levels. Keep optional
Easy simplification and piano gate changes separate: longer key-down time cannot
move an attack, and fewer attacks do not establish that the source had fewer
notes. Retain the original reference and audit all unaffected events.

Render raw and revised phrases with the same piano sound and fixed source clock,
including context and tails. Calibrate renderer latency once; per-candidate
alignment or time warping can conceal the defect. Compare melody alone, then
with bass/chords. A phrase is ready for the handoff when its essential attacks,
rests and releases have been reviewed or its unresolved passages are explicitly
identified. Compilation, pitch-frame agreement and perfect preservation of the
chosen reference do not replace this check.
