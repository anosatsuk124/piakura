# Phrase register and voicing

Read this before arranging for a limited keyboard. Choose an arrangement of voices within the range, rather than independently shifting source notes until they fit. Use [the checker and exception contract](voicing-contract.md) after compilation.

## Choose the voices together

1. For each observed phrase and harmonic interval, inventory the lead contour, bass movement, chord quality (including suspensions and omitted thirds) and characteristic figures from the source. Consider notes already sounding, not only attacks. Keep actual source note evidence for harmonic choices. Mark harmonic pivots from bass and harmonic-voice events before placing chords: anticipations and changes within a beat or bar need their own boundaries. A fixed half-bar or bar chord detector can suggest a chart, but verify its boundaries and essential colors against those events.
2. Try sensible keyboard windows and whole-phrase octave placements first. Evaluate the LH voicing against the lowest RH note reached during its entire hold. Favor smooth bass/inversion changes and recognizable melodic contour; extending a root-plus-third shell across a falling melody can create a crossing later in the phrase.
3. Test chord inversions, moving an inner chord tone to the RH, removing redundant doublings, source-supported substitutions, broken chords, or musically placed releases. Preserve lead onsets, gates, dynamics and rests. A local register exception is a last resort; document its effect on the phrase contour. Release decisions follow melody handoffs, harmony and phrase boundaries rather than a uniform short-gate cap.
4. Easy normally uses two-note harmonic shells and three notes when needed for quality. If a passage cannot retain the full shell, preserve its essential harmonic function across the passage through redistribution or an arpeggio. An isolated reduced attack can be appropriate; converting the whole accompaniment into single root/fifth notes loses the requested arrangement. Medium/Hard retain characteristic figures as well, within hand limits.

Choose shell tones across both hands: when the lead supplies the third, use the LH space for a source seventh or suspension instead of duplicating that third. A source major/minor seventh is a harmonic color to retain at every level, even when Easy needs a staggered entry or a third key. Removing it to obtain a safe root/third dyad changes the harmony. Resolve the register or gates of that color rather than dropping it.

## Recognize the failure patterns

- A source bass A well below a G# voice becomes A directly above G# after shifting octaves: the source's wide interval is now an adjacent semitone. Retain both A and G# across that harmonic interval: separate their registers, redistribute the G#, or alternate them with nonoverlapping gates. Replacing G# with C# makes a plain A-major shell and loses the source major-seventh color. Declaring the same root or avoiding the clash does not establish preservation.
- A compact LH chord can sit above the RH even though each hand independently passes span/polyphony checks. Evaluate both hands together. Favor the lower LH / upper RH layout; a real dialogue or voice transfer may justify a specifically annotated crossing.
- A held chord can be safe at its first attack and collide with a later melody note. Test every note boundary over the full hold. Shared-channel same-key handoffs still need a real release gap.
- Splitting a chord into successive attacks does not remove a clash if their gates still overlap. Review pedal separately so otherwise separated attacks do not accumulate into an unintended cluster.

## Finish the musical review

After the actual MIDI passes, compare each section with the source for lead contour, bass/inversion, chord quality, harmonic rhythm, characteristic accompaniment, and releases. At every verified harmonic pivot, account for the bass/root and the quality-defining third, seventh or suspension across both hands. A tone can be supplied by the lead, delayed or redistributed; record how it survives. Verify changes on their actual source ticks rather than only counting pitch classes anywhere in a half-bar. Correct lost colors or shifted changes before completion. Review every exception individually. Original source semitones need the exact source evidence required by the checker. A cramped keyboard alone is not a musical reason for a crossing.

Record the resulting musical decisions and unresolved passages in the private report. Refresh note IDs and hashes after any recompile. Deliver only scores with both a current PASS and completed source comparison; retain unsuccessful candidates as working evidence.

Make the color audit inspectable: for each harmonic interval, list its verified source root and quality tones, the source note IDs, and the actual compiled note IDs/times that retain each tone in RH or LH. Include delayed/broken-chord tones over the interval, rather than inspecting only its first attack. A missing root, seventh or suspension is an unresolved musical finding even when the MIDI's constraint report says PASS. Repair it or report that the requested music has not been preserved; do not turn the missing tone into a passing audit by relaxing the inventory.
