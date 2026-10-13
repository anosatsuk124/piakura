# Readable SakuraMML

`--mode readable` writes notation for people to read and edit. Unlike Pretty/Canonical, it quantizes to a declared beat clock, so input that is not aligned to it changes its original timing. How far notes moved appears in the `--readable-report` JSON. From now on, arrangements take this notation as their source of truth.

```text
// @section verse-a (20.40 s)
o5 l8 r4 d4. d c+ d& // 13: D
o5 l8 d4. r r d e e // 14: Bm7?
Sub{o4 l2 g a} o5 l8 e f g a b4 >c4& // 15: C
```

Clocks:

- `--clock score` (default): uses the input's tempo and time signature as they are; tick 0 is the start of bar `--first-bar` (default 1). Time-signature changes are unsupported and an error.
- `--clock grid`: counts the recording's beats. Give `--grid-bpm`, `--grid-downbeat` (the second at which bar 1 starts) and `--beats-per-bar`/`--beat-unit`. A transcription MML's `Tempo()` is a clock of seconds, not the music's beat, so use this clock for transcriptions and candidate MIDI. `--offset-seconds` is the recording second of the input's tick 0.
- Output uses `TimeBase(480)`. Tick 0 is the start of the bar containing input tick 0 (or the first note); notes before the first downbeat become a pickup in bar 0 or similar. That second is the report's `offset_seconds` (the value to give the piakura-review layer). The grid tempo is written as an integer `Tempo(150)` if the drift by the end of the song stays under 15 ms, otherwise as a decimal `Tempo={150.01}`.

Notation:

- One bar per line. Each line ends with `// bar: chords`; a section gets the heading `// @section label (seconds)` (from the `--sections` array, or a review spec.json with `--section-set`). Consecutive identical bars fold into `[n …] // a-b` (`--no-fold` disables this).
- The prose of the header and section comments follows `--language`; tags (`@clock`, `@key`, `@section`), chords and bar numbers stay the same in every language.
- Onsets snap, per track and per beat, to a 16th-note grid (coarser with `--subdivision 8|4`) or an eighth-note triplet grid. A beat becomes triplets only when at least 2 inner points carry onsets and the drop in squared error exceeds `--triplet-penalty` (beats², default 0.004). Quarter-note triplets spanning 2 beats use the same test. This keeps a transcription's ~10 ms jitter from turning 16ths into triplets. `--no-triplets` disables triplets.
- Lengths are note values (`1 2. 2 4. 3 4 8. 6 8 12 16 24 48`; others are joined with `^`). Each voice's `l` is its most frequent non-dotted value used at least twice. One beat of eighth-note-triplet single notes/rests is `{c r e}4` (always write the group's length; no chords inside).
- Notes that start together and end together form a chord `'ea>c<'`. Undo an octave raised inside a chord before closing it, so the octave before and after the chord stays the same.
- Overlapping notes are split into voices: the voice with the most notes (single notes or chords) is the main line, the rest become `Sub{o.. l.. …}` on the same line. TR stays the input track (keeping piano TR1 = right hand, TR2 = left hand). Inside `Sub`, leave `v`/`q` unchanged, and after `Sub` rewrite the main line's `o`/`l` (upstream `Sub` restores only the time; `o/l/v/q` leak out).
- A main-line single note crossing a barline becomes a tie: `f2&` → `f4` on the next line. The closing note is the first note executed on the next line; if another voice of the same track has an onset within the tie, the tie breaks into a portamento, so that note and any chord crossing the barline move into `Sub` and run past the bar. Start no line with `^`: combined with the previous line's trailing comment it is an error.
- One `q` per track: the most frequent "sounding length / interval to the next onset" of legato notes (steps of 5, 50–100). Write notes clearly shorter than that with their own note value and a rest. Always release before the next onset of the same channel and pitch. `--gate exact` adds `c4,%432` to notes that do not fit.
- Write `v` at the start of a line only when the bar's median velocity moves by 8 or more (`--velocity track|exact` are also available).
- The key is estimated with Krumhansl-Kessler, bar by bar: five-bar windows score the 24 keys, and a key change must pay for itself over several bars, so a passing secondary dominant or a phrase leaning on the relative minor stays in the key. A passage whose best key is the relative of a key heard earlier keeps that earlier key. The opening key goes in the header (`// @key D major (estimated)`); each modulation gets `// @key E major (estimated)` above its first bar in every track, after that bar's `@section` heading. `?` after the key marks a low-confidence one. The key in force decides the direction of accidentals (`c+` or `d-`; a minor key's leading tone is always sharp), the spelling of chord names and the degrees. A note tied across a key heading keeps the spelling of its onset. `KEY()` transposes upstream, so it is never written. Chord names are estimated per bar from the written lengths of all tracks (split into half bars only when both halves are clear and fit much better), with `?` on low-confidence ones. Input of a single melody line gets no chord names. `--chords names|roman|both|none`.
- Not written: controllers, pitch bend, text meta events, SysEx, the reserved Marker for End Of Track, release velocity. Their counts are the report's `dropped`.

Main report fields: the drift between the clock and the written tempo `drift_ms`, `offset_seconds`, the opening `key` and, when the key changes, every key span in `keys` (`[{"bar": 1, "key": "D major"}, {"bar": 102, "key": "D minor"}]`), note counts (merged, unison, trimmed, moved ornaments, voice-trimmed), onset and end deviations `onset_ms`/`end_ms` (p50/p95/max/signed mean), `velocity` differences, the number of triplet beats, the number of chord `?`s, the 20 notes that moved most (`worst`), every note that moved by half a 16th or more (`moved`), and the list of merges, trims and ornament moves (`events`, notes as track/on_order). A signed mean above 1/4 of a 16th gives a warning that the bar start or the clock is wrong.

Invariants (checked by tests): the predicted notes (`Result.Predicted`) and their lines match upstream's compiled result and `--note-lines`. Reading the output back with `--clock score --first-bar <first_bar>` reproduces the same text. For on-grid input, pitches and onsets match; with `--gate exact --velocity exact`, ends and velocities match too.
