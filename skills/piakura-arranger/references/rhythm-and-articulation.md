# Rhythm, tuplets and piano articulation

Use this reference when notes sound disconnected, repeated notes sound hesitant,
a phrase slows locally, tuplets are plausible, or Easy needs simpler melody.
Resolve three different decisions: **when to attack**, **when to release**, and
**which attacks the arrangement needs**.

## Diagnose the phrase before editing

Compare melody alone and with accompaniment on the same source clock. If the
same defect occurs at several difficulty levels, inspect their shared melody
reference first. Exact preservation can reproduce an inaccurate reference.
Return audio-derived timing questions to [rhythm reconstruction](../../piakura-transcription/references/rhythm-reconstruction.md).

Record the phrase's beat span, attack count, inter-onset intervals, and signed
displacements from supported lead attacks. Growing displacement with an
unchanged backing pulse can indicate accidental local slowing; constant
displacement can reflect intentional phrasing or an alignment error. Neither
pattern alone proves a correction. Inspect the pickup, internal weak attacks,
rests and arrival, including repeated occurrences and crop boundaries.

Test straight, dotted, triplet/other tuplet and swung interpretations as whole
groups. Choose a supported grouping before calculating individual ticks. Six
attacks are not automatically a sextuplet: six eighths occupy three quarter-note
beats, while six equal notes inside a half note occupy two. A triplet is an equal
division of its enclosing span; swing alternates long/short divisions. Retain
expressive exceptions when the source supports them.

## Express the chosen grouping in SakuraMML

The brace suffix specifies the **whole group's duration**, not each note:

```text
o5 q90 l8 c c c c c c    // six straight eighths: three beats
o5 q90 {cde}4            // three equal notes in one quarter-note beat
o5 q90 Div{cde}2         // three equal notes in two beats
o5 q90 {cdefg}4          // five equal notes in one beat
o5 q90 {cdefga}2         // six equal notes in two beats
o5 q90 c%640 d%320       // at TimeBase(960): explicit 2:1 long-short
```

Prefer ordinary lengths, ties, rests and `Div{...}` / `{...}` for a supported
musical pattern. In readable scores a group stays on one line with its group
length written (`{c d e}4`), and a tie across a bar line is `&` followed by the
next executed note ([piakura-readable-mml](../../piakura-readable-mml/SKILL.md)). Keep exact `%tick` lengths or `Time` anchors for deliberate
exceptions. Braces distribute time; they do not infer which rhythm fits audio.
Use implicit inner note lengths for these equal-slot examples. Compile and read
the Go sidecar: check each onset, gate, group end and the following note. The
pinned compiler integer-divides the span among slots, then restores the exact
group endpoint. A PPQN divisible by the needed subdivisions avoids internal
rounding; nested groups need their own check. Conversion itself stays lossless.

The pinned compiler's documented `{c^d}4` shorthand does not produce the intended
2:1 pattern in the compiled fixture: the second note reaches the group endpoint
and overlaps the following note. Use checked explicit lengths for that weighted
pattern, for example at `TimeBase(960)`:

```text
Time(9600) c%640 d%320 e4    // checked 2:1 weighting
Time(11520) q50 {cde}4 f4    // triplet with a shortened gate
```

The project's skill test compiles these lines and checks every onset and gate;
the pinned compiler itself is unmodified.

`q90` holds a key for 90% of its allocated note length; `q%173` holds it for
173 ticks. Neither changes the next onset or reduces the attack count. A gate
edit cannot repair a misplaced onset. A nearly continuous series of repeated
keys may benefit from a brief release, while too-short gates create stuttering.
Select articulation locally, respecting phrase rests and shared-key handoffs.
When cause is uncertain, render timing-only and gate-only alternatives before
combining edits. A new gate is a musical change under strict preservation.

## Adapt for listening and two-hand playing

Begin with the supported phrase, including the holds and defining ornaments in
[phrase design](phrase-design.md#protect-holds-and-defining-ornaments).
Piano articulation can need different key releases even when the source is easy
to play. For disconnected phrases, first compare a release-only adaptation that
keeps supported pitches and attacks, structural holds, ornaments and intended
breaths. Choose continuity voice by voice using [resonance](phrase-design.md#dynamics-articulation-and-resonance).
If the phrase still exceeds the requested difficulty after redistributing
accompaniment, compare a local melodic reduction. Preserve pickup, accent,
contour and arrival; identify the playing problem it solves. Judge repeated
attacks and runs as gestures, not by a global inter-onset threshold. Keep the
source transcription and chosen adaptation distinct.

For sung phrases, review the gaps left after reduction as well as the notes.
Use [vocal-to-piano adaptation](vocal-to-piano.md) to preserve continuity and the
climax. Gate percentage alone cannot fill a following rest.

Keep the source transcription intact for an arrangement-only change. Before
editing the arrangement, declare the affected source note IDs/times and their
replacement pitches/onsets/durations in a separate level-specific retention
contract. Compile that contract from the curated reference plus the declared
edits, not by extracting an expected answer from the finished arrangement.
Check the Go sidecars exhaustively: all undeclared reference and accompaniment
events must remain unchanged; all replacements must match the declared values.

Run the usual strict validation against this explicitly labelled contract and
retain a comparison against the original reference, including expected missing
notes and duration changes. Report both scopes; contract PASS is not original
100% retention or source accuracy. A source-timing correction instead needs a
new verified transcription handoff and corresponding updates at every affected
level. Existing user authorization is sufficient; do not ask for it again.

Deliver matched before/after clips with context, editable scores and the actual
validation reports. Keep listening acceptance separate from compiled timing,
reference retention and physical-constraint PASS.
