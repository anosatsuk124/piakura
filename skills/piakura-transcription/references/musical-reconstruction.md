# Musical reconstruction from noisy evidence

## Recording context and evidence order

Identify the exact recording, including live/studio, original/cover, tuning/transposition, shortened video edit and instrumental/vocal version. Official credits and release pages help establish instrumentation and genre. User-supplied scores can be references but are not automatically aligned ground truth. Unknown key, meter or form stays unknown until supported. When online metadata is absent, proceed from observed audio/MIDI and label the estimates.

Prefer evidence in this order: the recording and stable acoustic features; a clearly isolated source or repeated occurrence of a phrase; independent model agreement; continuity and harmonic context; general stylistic expectation. Separation can erase notes and introduce bleed, so compare a stem with the original mix. Repeated sections may intentionally vary; repetition is evidence, not a template to paste blindly. State what was inspected: never claim listening when only numeric audio features were available.

For each disputed passage record its source time/measure, candidate interpretations, evidence, chosen edit and remaining uncertainty. An edit can delete, merge, split, move, reassign a role or add an inferred note. Keep evidence concise at phrase level unless an individual note matters. Keep raw audio and model MIDI unchanged.

## Melody and voice continuity

Follow the vocal or instrumental line through pickups, rests, repeated attacks, held arrivals and lead handoffs. Trace it inside simultaneous chords as well as isolated notes; a model channel can mix melody and accompaniment. Assign roles from phrase continuity and source evidence. Highest pitch, program, simultaneous-note count or distance from a selected attack alone cannot decide ownership. Preserve the recovered instrumental response before the arranger chooses its difficulty treatment.

An isolated octave excursion is suspicious when the same motif, the fundamental contour and neighboring notes favor one register. A real octave leap with an audible attack remains valid. A stable fundamental with several simultaneous harmonic multiples can indicate overtone false positives, but actual octave doubling must not be removed merely because the frequencies are related.

Review pitch class and register separately. A symbolic model can recover the
note sequence while placing it an octave away. Compare octave alternatives
against stable source-derived F0 and, where available, an independent F0 model;
do not apply a fixed octave shift to an entire recording. Retain the symbolic
pitch class when a scoop, vibrato or portamento moves the median F0 between
notes. A rounded F0 median alone must not replace a supported passing or
destination note. Disagreement is a reason to inspect the contour and neighboring
attacks, not to assemble a union of both models' notes.

Vibrato/portamento can fragment one sung note into chromatic MIDI pieces. Merge only when the contour, absence of renewed attacks and phrase context support one note. Preserve repeated syllables/attacks at the same pitch. A short, weak event with no attack and no repeat support is a stronger deletion candidate than a short event alone.

For a sweep, slide or rapid instrumental passage, identify the gesture before
freezing every decoder fragment as a required melody note. Record its anchors,
motion and uncertain internal attacks. When preparing a piano adaptation, follow
the [gesture and clutter review](../../piakura-arranger/references/gestures.md).

Missing melody is more consequential than a missing inner voice. Where the melody is unresolved, compare a separated vocal/lead stem or an independent inference before filling from expectation. When audio is absent, retain disputed notes and mark hypotheses rather than manufacturing certainty.

## Meter, rhythm and duration

Estimate local beats and downbeats; test half/double tempo and pickup alternatives before declaring a meter. A constant-tempo MIDI exported by an AMT model may merely encode seconds. It is not evidence that the music has that tempo. Map seconds to beats using verified anchors/tempo changes before notation quantization. Preserve source seconds and record the map.

Evaluate straight subdivisions, triplets and swing separately. Prefer the least complex rhythmic description that explains observed attacks and repeated phrases, while retaining supported anticipations and syncopations. Do not snap every onset to sixteenths or delete offbeats to improve grid statistics. Rubato and tempo changes need local maps, not whole-song stretching.

Read [rhythm reconstruction](rhythm-reconstruction.md) for weak attacks, missing notes and irregular model timing. A model timestamp is a proposal, not a measured key press. Keep acoustically supported lead onsets until that voice's own attacks support moving them. A well-fitted drum grid establishes the pulse, not where a singer must attack; consistently late singing can be intentional. Express off-grid timing with exact ticks in SakuraMML when needed. Before freezing a rhythmic correction, compare the edited and raw onsets on the same audio clock and cite lead-specific attack evidence for the displacement. A simpler rhythm or a constant early/late bias alone is insufficient.

Distinguish score duration, key-down duration and recorded decay. Reverb/sustain often stretches model offsets; vocals do not have piano key-down timing. Infer useful articulation from phrase continuity, repeated attacks and harmonic changes, and document that reconstruction before freezing the handoff. Do not use a universal gate cap. For downstream piano, accompaniment may release before a shared key is handed to melody; the melody contract itself remains intact.

Preserve differentiated releases when the audio does not resolve them; replacing a whole melody with legato changes articulation, even if its onsets are correct. A peak continuing through a bass attack can be the previous melody note's decay. Confirm a renewed attack in that pitch/voice before treating it as a repeated note.

When a listener accepts a short candidate, retain that exact score, render hash
and source interval as a local regression constraint. Preserve its internal
attacks, pitches and releases when integrating it into the full score; handle
crop-boundary sustains separately. The approval covers that excerpt, not every
output from its model or a measured whole-song accuracy percentage.

## Harmony and bass

Infer harmony over its rhythm of change rather than each short event. Consider bass motion, sustained notes, accented melody, characteristic thirds/sevenths, inversions and voice leading together. Bass is not always the chord root: preserve slash chords, pedals and stepwise lines when supported.

Use major/minor quality, seventh quality, sus/add tones and omissions as alternatives. With C and G only, record an open fifth or uncertain quality unless E/E-flat is supported elsewhere. With a stable sus sound, do not insert a third to make a textbook triad. Do not convert every bass onset into a new chord or hold accompaniment across a confirmed harmony change.

Inspect non-chord tones by approach, metric placement and departure: passing and neighbor tones, appoggiaturas, anticipations, suspensions and pedal tones can be essential. For example, a brief D between C and E over C harmony is consistent with a passing tone; its non-chord status is not evidence of a false detection.

Allow applied dominants, modal mixture, borrowed chords, chromatic bass, modal passages, blues inflections and genuine modulation. Analyze repeated chromatic evidence before “correcting” a recording into its initial key. Do not infer a modulation from one altered note or require every pop progression to resolve with classical functional harmony.

References for terminology and counterexamples: [non-chord tones](https://musictheory.pugetsound.edu/mt21c/NonChordTonesIntroduction.html), [modal mixture](https://viva.pressbooks.pub/openmusictheory/chapter/modal-mixture/), [modulation](https://openmusictheory.github.io/Modulation.html). These are analytical tools, not an error detector with guaranteed accuracy.

## Uncertainty and handoff

For ambiguous tonality, jazz, atonal music or percussion-heavy textures, give more weight to contour, register, recurring patterns and rhythmic layers. A tonal model must be able to abstain. Mark uncertain chord labels rather than harmonizing every measure conventionally. Reduce assumptions locally; one ambiguous bridge does not invalidate clearly tonal verses.

The reconstruction preserves the musical material without assigning hands or enforcing difficulty quotas. Pass melody, bass, harmonic rhythm, supported chord colors and hooks to the arranger. A sparse reliable harmony is preferable to invented dense voicing. Keep uncertainty available so later arrangement does not present a speculative chord as a recovered fact.
