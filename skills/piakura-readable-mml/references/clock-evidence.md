# Clock evidence

A grid clock needs a pulse (BPM and beat phase) and a downbeat (which beat is beat 1). A beat tracker or a fitted pulse gives the first; it does not give the second. A downbeat placed one or three beats off still quantizes cleanly, so the report alone will not catch it: every line then starts mid-phrase and every chord change lands on beat 4.

## Pulse

Take the BPM and phase from the measured clock (`clock-analysis.json`, `beat-clock-fit.json`, Beat This beats, or a fit to source attacks). Check its residuals against strong attacks. A transcription MML's `Tempo(150)` is a seconds clock (2400 ticks = 1 s) whatever the music's tempo.

## Downbeat

Score each candidate phase (0 to `beats_per_bar − 1` beats after a pulse origin) with independent kinds of evidence, and keep the phase they agree on:

- **Harmonic change**: chord or bass changes cluster on beat 1. Histogram the change times of the harmony evidence by beat in the bar.
- **Bass and left-hand attacks**: a held bass or a block chord per bar starts on beat 1; arrangement LH bar attacks repeat at one phase.
- **Phrase and section starts**: section boundaries fall on bar lines and group into 4- or 8-bar phrases. A boundary a beat or two early is a pickup.
- **Model downbeats**: Beat This downbeats, when available, as one vote.

Melody onsets are weak evidence: vocal phrases often start on pickups.

Bar 1 is the first downbeat at or after the music starts; earlier notes fall into bar 0 (or earlier) as pickups. Record the counts behind the choice, for example "146 of 184 harmonic changes on beat 1 at +3 beats; LH bar attacks at the same phase; sections start at bars 13, 21, 29".

## After generating

The report's signed mean onset shows a constant offset left in the phase; shift the downbeat by that amount (under a sixteenth). Growing deviations or a large `drift_ms` show a BPM error. A grid review session draws its bar lines from the same `origin_seconds`, so the reviewer sees the bars the readable score uses.
