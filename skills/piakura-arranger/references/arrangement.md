# Musical priorities

Start with the recognizable lead, bass movement and harmonic rhythm. Transfer instrumental roles into piano voices rather than concatenating all channels. Treat drum channels and XG bank 126/127 as rhythmic information, not literal pitched keys. Source program, density and register are evidence for a role, not proof of the melody.

Easy: simplify competing accompaniment and doublings while retaining the tune, phrase rests, hooks and harmonic changes. Choose chord tones for their source roles; the bass, third, seventh or suspension may matter more than a complete chord. Use the available hand capacity where those roles need it. Medium: retain characteristic accompaniment motion and harmonic color with the lead. Hard: develop independent voices where supported and playable. These levels describe demands on the player, not fixed accompaniment patterns. Use [phrase design](phrase-design.md) for protected holds and gestures, and [rhythm and articulation](rhythm-and-articulation.md) when the lead itself needs adaptation.

The note-ratio targets in [difficulty model](difficulty-model.md) are review guidance. A sparse passage may need no added notes. A dense ensemble may require more reduction than the ratio suggests. Melody retention and playable hand allocation take priority over meeting a quota.

For hesitant repetitions, tuplets, gate changes or authorized Easy melody
reduction, read [rhythm and articulation](rhythm-and-articulation.md). An unchanged
fast lead does not become easy merely because its accompaniment is sparse.
Separate source-timing repair, piano articulation and difficulty reduction;
validate each against its declared reference or arrangement contract.

## Reconstruct piano accompaniment

An audio-derived reference can have a usable melody while bass, chord labels and
their timestamps remain uncertain. Recheck harmonic changes on the source clock;
short-window melody repair does not also repair a retained long-generation chord
track. Recover the passage's bass attacks, held tones, anticipations and answering
figures before choosing piano voicings. A chord chart alone loses these roles.
Reconstruct unresolved passages locally; retain supported movement elsewhere.

Choose root, chord quality and intended bass independently. A slash chord is a
deliberate bass choice, not an accidental result of fitting chord tones into a
register. Keep the declared bass below the inner voices; never fold an upper
tone underneath it merely to pass a span limit. Redistribute, omit a doubling,
change the whole voicing or alternate bass and chord attacks instead. Avoid
crowded low thirds, unsupported extensions and doubled passing bass tones.
Connect adjacent voicings with small inner-voice motion and preserve supported
suspensions and chromatic harmony.

### Review collisions between melody and accompaniment

Inspect every sounding vertical combination across both hands, including held
notes, repeated accompaniment attacks and pedal/release tails. Flag semitone
neighbours, minor ninths and octave-displaced versions for musical review; low
register, long overlap, strong attack and close voicing increase their salience.
Record the two pitches, roles, overlap interval and expected resolution rather
than treating a pitch-class difference as an automatic deletion rule.

First check source pitch/register and chord-change timing. A stale chord third
under a melody anticipation, an added upper chord tone ringing into its semitone
neighbour, or a wrongly inferred major/minor third can produce unintended
roughness. Review melody alone, accompaniment alone and their combination at
the reported time. Key-down intervals establish overlap but do not bound all
audible resonance. Physical-constraint PASS does not assess consonance.

Keep supported passing tones, suspensions, appoggiaturas, altered dominants,
major sevenths and deliberate clusters. Judge accent, duration, voice leading,
resolution and the requested style; a supported dissonance may be essential.
When an optional accompaniment tone causes the unwanted clash, preserve the
lead and harmonic function while omitting that tone, releasing it earlier,
moving the voicing or using a temporary suspended/open voicing. Correct a
mistimed chord when evidence supports that instead. Merely moving a conflicting
pitch by an octave can leave the harmonic conflict intact. Hard may also need
fewer notes; adding a third or extension to every attack is not a requirement.

Document the local voicing decision, compile again, check every unaffected
event and compare the complete phrase with the same piano sound. Inspect other
levels for the same harmonic issue without copying a deletion into passages
where the rhythm, register or resolution differs.

Follow the source groove when placing bass and chord attacks, including offbeats,
rests and held notes. Use the supported beat clock for reconstructed timing.
Let texture changes follow the phrase; steady repetition can itself be essential.
The melody's timing is the readable reference's: the user adopted quantized
readable scores as the editable form (2026-10-08). Where its report shows a
deviation that carries the phrase (a deliberate push or drag, a grace note),
restore it explicitly in the score with a comment. A converter must still
preserve its input; only `--mode readable` quantizes.

Make the readable MML the authoritative editable score: bar lines, phrase and
chord comments (`Name(Degree)`, see
[piakura-readable-mml](../../piakura-readable-mml/SKILL.md#chord-comments)), note values, rests
and chords throughout, with exact ticks only for restored exceptions. JSON
is analysis/provenance, not a replacement score that silently overwrites later
MML edits. Render the accompaniment alone and in context when checking bass
placement, voicing and groove; hard-constraint PASS does not verify these.

For glissandi, slides, rapid runs or suspected ornamental clutter, read
[gestures and spurious notes](gestures.md) before simplifying the passage or
freezing its individual notes as the melody-retention contract.

Use section comments derived from observable texture/phrase changes. If the form has not been confirmed, labels such as `section-03` or `instrumental-lead` are better than asserting verse/chorus. Keep source channel annotations near retained phrases and explain meaningful omissions/register shifts. The compiled SMF, not a comment, is the basis of validation.

Sakura octave numbers follow MIDI: `o5 c` = MIDI 60. `l4` is a quarter note. `q90` is proportional key-down duration; `q%173` is exact tick duration. `q` does not round onsets. Overlapping independent voices may require explicit `Time` anchors; retain them where necessary. Ordinary notes can express exact unusual rhythms with `%tick` lengths. Use `Random`-free scores so revalidation describes the delivered artifact.

Validate hand occupancy using key-down duration. A long pedal sound does not require holding the key, but sustain can still obscure articulation: review pedal musically. PASS covers the documented constraints; sight-reading, fingering, hand size, harmonic correctness and perceived difficulty require musical review.

For held-hand order, phrase register selection and source-grounded dissonance review, use [voicing.md](voicing.md). Preserve harmonic identity and characteristic accompaniment when reducing a constrained-keyboard score; note count is not a substitute for those roles.
