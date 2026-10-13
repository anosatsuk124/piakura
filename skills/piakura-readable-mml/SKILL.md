---
name: piakura-readable-mml
description: Write readable SakuraMML (one bar per line with note values, chords, triplets, Sub voices, ties, repeat loops, section and chord comments) from MIDI or one-note-per-line MML, and author scores in that form. Use when people will read or edit a score, when review MML is unreadable, or before arranging with piakura-arranger.
---

# Readable MML

Readable MML is the editable form of scores in this project: one bar per line, a [chord comment](#chord-comments) at the end of each line, note values instead of ticks. `smf2sakura --mode readable` writes it from any SMF by quantizing to a musical clock; [canonical-mml.md](references/readable-format.md) holds its rules, report fields and invariants. Quantizing moves notes, so every readable score comes with its report, and you account for what moved.

Usually reached from another piakura skill inside a piakura job; when invoked on its own without one, start from [piakura](../piakura/SKILL.md) so the user's consent, settings and `$WORK` exist.

Script paths below are relative to this skill's directory; `../piakura-arranger/scripts/tool.sh` runs the installed tools.

## 1. Fix the clock

The bars must be the music's bars; a line per wrong bar is unreadable.

- MIDI made on a musical tempo map (human-made files, compiled scores, earlier readable output): `--clock score`. Check that the first bar line is a downbeat; give `--first-bar 0` when tick 0 starts a pickup bar.
- Transcriptions and model MIDI, whose `Tempo()` is a seconds clock: `--clock grid --grid-bpm B --grid-downbeat S`, where `S` is the recording second of bar 1. Read [clock evidence](references/clock-evidence.md) to fix `B` and `S`.

Done when the downbeat rests on at least two independent kinds of evidence, written down where the score's evidence lives (handoff `evidence.md`, the arrangement report or the review grid `note`).

## 2. Generate

```bash
bash ../piakura-arranger/scripts/tool.sh smf2sakura score.mid --mode readable --clock grid --grid-bpm 150.0067 --grid-downbeat 1.2207 \
  --sections sections.json --chords both --language en \
  -o score.readable.mml --readable-report score.readable.json --line-map score.readable.lines.tsv
bash ../piakura-arranger/scripts/compile.sh score.readable.mml score.readable.mid
```

`--sections` takes a list of `{label, start}` in recording seconds, or a piakura-review `spec.json` with `--section-set`. `--chords names|roman|both|none` chooses the bar comments. `--language` is the language of the comments' prose, the job's [language](../piakura/references/language.md); tags and chords stay as they are. `--line-map` lists each input note's `track`, `on_order` and output line.

## 3. Account for what moved

Read the report against the clock:

- A warning about a constant offset, or `onset_ms.mean_signed` beyond a quarter of a sixteenth, means the downbeat or BPM is off: return to step 1.
- `drift_ms` and deviations that grow along the piece mean the tempo differs: refit the BPM or split the piece at the tempo change.
- Every note in `worst` above half a sixteenth, every merged or unison note and every moved ornament is a decision: accept it as notation, or restore it by hand in the readable score (an exact `%tick` length or a `Time()` exception with a comment saying why).

Done when every such note is accepted or restored and the report and the decisions are saved beside the score.

## 4. Polish without changing notes

Replace a `?` chord with a [chord comment](#chord-comments) your harmonic evidence supports, fold phrases into `[n … : …]` loops, add headings. Compile before and after; `bash ../piakura-arranger/scripts/tool.sh mididiff before.mid after.mid` must PASS.

## 5. Export notation (when asked)

`mml2score` reads a readable score as staff notation — key signatures from `// @key`, accidentals as spelled, voices for `Sub`, ties, triplets, chord symbols from the bar comments — and writes MusicXML for notation software such as MuseScore, or LilyPond:

```bash
bash ../piakura-arranger/scripts/tool.sh mml2score score.readable.mml --to musicxml --chords both -o score.musicxml
bash ../piakura-arranger/scripts/tool.sh mml2score score.readable.mml --to lilypond -o score.ly
```

`--to mml` tidies the text instead: every bar it can is rewritten one bar per line with written values, gates and the key's spellings, and every sound stays exactly as it was; folded loops and bars it cannot write so are kept and named on stderr. Compile and compare before replacing a score with it.

It refuses text outside the readable form (`KEY()`, macros, `DirectSMF`) with `file:line:col: error code: detail` and exits 1; fix the score, not the tool. `--chords names|roman|both|none` chooses what the bar comments become. `--holds pedal` (the default) writes each hand of a piano as one voice of chords, each up to the next one, with pedal marks where tones sound on; `--holds voices` writes every `Sub` as its own voice at its own lengths. A time signature may change on a bar line (`TimeSignature(2,4)` in `TR(0)` at that bar's tick, and back); the notation, the review page's score and its edits follow it, but a change inside a bar is an error.

## Writing readable scores by hand

Arrangements and corrections are written in the same form. Keep upstream's semantics in view:

- One bar per line, ending in a [chord comment](#chord-comments); `// @section label (seconds)` above a section's first bar, and `// @key E major` above the first bar of a new key.
- A `{x y z}4` group sits on one line, states its group length and holds single notes or rests: the pinned compiler counts each chord tone as a slot.
- A note tied across a bar line ends its line with `&`, and the next note upstream executes is its continuation at the start of the next line. A `Sub` or another note in between turns the tie into a portamento, so a crossing chord or a crossing note under another voice goes into a `Sub` that overflows the bar instead.
- A `Sub{o.. l.. …}` states its own `o` and `l`; the main line states `o` and `l` again after it, because `Sub` restores only the time position. Keep `v` and `q` outside `Sub`.
- The key goes in a comment: upstream `KEY(n)` transposes. Comments use `//`, since `///` becomes a MIDI text event. Lengths continue with `^` inside a token (`c2^8`), never at the start of a line.
- Spell accidentals in the direction of the key in force, as `smf2sakura` does: `e-` and `a-`, not `d+` and `g+`, in A♭ major; a minor key's leading tone is sharp. The notation respells a note of the key written against it, but a note outside the key shows as spelled.
- <a id="written-values"></a>Write each note's written value and put an early release in its gate: `c4,%456` (or the track's `q`), never a shorter length and a short rest such as `c%456 r%24`. Keep onsets on the beat grid; offset one by a few ticks (`Sub{r%17 …}`) only for a deliberate spread such as a rolled chord, with a comment. The notation counts such short gaps and small offsets as the performance's, but the text stays hard to read and edit.
- <a id="voices"></a>Keep a line that continues into the next bar in the same place: the main line, or the same `Sub` counting from the left, on every line it plays. Write tones that start and end together as a chord (`'ceg'4`), not as separate `Sub`s. Which line is the main line, which hand plays it, and how a chord spreads across both hands remain arranging decisions: a chord across the hands is written in each hand's track, and the score shows its parts on the two staves.

For review, publish the readable score as its own layer with `offset_seconds` from the report (see [piakura-review](../piakura-review/SKILL.md)); the review UI also shows a generated readable view of every layer.

## Chord comments

Every bar line ends in `// bar: Name(Degree)`, the form `smf2sakura --chords both` writes, so the review UI and its export video can show the sounding chord, its degree and the key in force from any score ([piakura-review](../piakura-review/SKILL.md)):

```text
// @key D major
o5 l4 a a8 a d c+8& // 37: Gadd9(IVadd9)
o5 l8 g2 <b >e g a& // 38: GM7/D(IVM7) - A(V)
o5 l4 a a f+8. g8. // 39: F#m7/E(IIIm7)?
```

- **Name**: root, quality and, for an inversion, `/bass` (`GM7/D`). Qualities: none (major), `m`, `7`, `M7`, `m7`, `m7b5`, `dim`, `sus2`, `sus4`, `add9`, `aug`; write a richer chord as its nearest quality and spell the colour in a phrase comment.
- **Degree**: the root counted from the tonic of the `// @key` in force on the major scale (`I bII II bIII III IV #IV V bVI VI bVII VII`), plus the same quality and no bass (`IVM7`). A minor key counts from its own tonic (`Im`, `bIII`, `bVII`).
- **Key changes**: where the music modulates, write `// @key E major` (or `minor`) on its own line directly above the first bar line of the new key, in every track; degrees from that bar count from the new tonic. The review UI and its export video show the key in force next to the chord, so a wrong or missing heading misreads every degree after it. Move or remove a generated heading your harmonic evidence contradicts, and keep the relative major/minor of the song's key as the song's key unless the music cadences there.
- **Halves**: a bar whose harmony changes mid-bar holds two chords joined by ` - `, at most; place a quicker change on the half it falls in.
- **Unsure**: `?` after the whole chord (`F#m7/E(IIIm7)?`); a bar with no chord evidence reads `?`.
