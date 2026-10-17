---
name: piakura-upgrade
description: "Upgrade work made by an older piakura so it reads as the current one writes it, and hand it to keyroam. Use when readable MML still has `// @key`, `// @section` or bar-comment chords (`// 12: Bm7(VIm7)`), when mml2score warns `chord-syntax`, or when a published review session should open in keyroam as a `.keyroam.zip` package."
---

# Piakura upgrade

Older piakura wrote keys, sections and chords as `//` comments: `// @key D major (estimated)`, `// @section verse-a (20.40 s)` and a chord list at the end of each bar line (`// 12: Bm7(VIm7) - A(V)`). The current form writes each where it applies as an anchored comment, `/** @key D:maj */`, `/** @section verse-a */`, `/** @chord B:min7 roman=VIm7 */`, with chord values in the Harte grammar ([chord comments](../piakura-readable-mml/SKILL.md#chord-comments)). Old scores still read, but only the anchored form carries over to keyroam, so upgrade every score you will keep working on, then the review sessions.

Script paths are relative to this skill's directory; `bash ../piakura-arranger/scripts/tool.sh` runs the installed tools (`T` below). Inside a piakura job work in its `$WORK`; otherwise in the directory the user names, after starting from [piakura](../piakura/SKILL.md) if the tools are not installed. The upgrade changes comments only: every sound stays as it was, and each step below proves it.

## 1. List the work

List the readable scores (arrangement levels, readable references, corrected transcriptions: the `*.mml` files a review layer or a handoff names) and the review sessions (`review/review.json`). A score needs the upgrade when it has a `// @key`, a `// @section` or a bar comment with chords:

```bash
grep -rlE '^[[:space:]]*//[[:space:]]*@(key|section)[[:space:]]|//[[:space:]]*-?[0-9]+(-[0-9]+)?:[[:space:]]*[^[:space:]]' --include='*.mml' --exclude-dir=objects "$WORK"
```

The review's `objects/` hold published revisions; the tool owns them, and step 4 replaces them with a new revision.

Done when every score and session is on the list with what it needs.

## 2. Upgrade each score

```bash
$T mml2score score.mml --to anchored -o score.anchored.mml
```

It rewrites the comments in place, reads the result back and proves that every sound and every bar's key, chords and sections are unchanged; stderr counts what it rewrote and names what it left. A kind it cannot place stays in the old form, whole, with notes:

- `upgrade-unplaced`: a chord falls where no main-line note or rest of its line starts (a held note across the half bar, a bar comment on a line without notes). Write the chord yourself where it starts in another part's line, or split the note with a tie, and run again.
- `upgrade-folded`: a loop over several lines (`[2 …` to `]`) whose passes have different chords. Write the loop out a bar a line, and run again.
- `upgrade-x`: a chord Harte cannot say, written as `/** @chord X text=… */`; replace it with the nearest Harte chord when your harmonic evidence names one.
- `upgrade-key`, `upgrade-section`, `upgrade-chord`: that kind stayed old; the earlier notes say why.

Then prove the sound and read the score:

```bash
bash ../piakura-arranger/scripts/compile.sh score.mml before.mid
bash ../piakura-arranger/scripts/compile.sh score.anchored.mml after.mid
$T mididiff before.mid after.mid
$T mml2score score.anchored.mml --to json -o /dev/null
```

Replace `score.mml` with the upgraded text once `mididiff` passes and `mml2score` prints no `chord-syntax`, `key-syntax` or `comment-unplaced` warning. Rewrite the header line that explained the old bar comments, if the score has one, to say keys and chords are estimated. Done when every listed score is replaced and passes.

## 3. Fix chord values

A score already in the anchored form can carry values outside the Harte grammar (`/** @chord Bm7 */`); `mml2score` warns `chord-syntax` for each and leaves it out. Rewrite each as Harte (`B:min7`, `F#:7/b7`, `G:maj(9)`), or as `X text=…` when no Harte chord says it. Done when `$T mml2score score.mml --to json -o /dev/null` warns no `chord-syntax`.

## 4. Republish and package the reviews

A published revision keeps the comments it was published with. Publish the session again so its layers and readable views carry the upgraded scores, answering nothing:

```bash
$T piakura-review publish "$WORK/review/spec.json" -m "comments in the current form" --responds-to none
```

Then write a keyroam package for each layer the user wants to open there (an arrangement level, the corrected transcription):

```bash
$T piakura-review package "$WORK/review/review.json" --layer easy -o "$DELIVERY/<slug>-easy.keyroam.zip"
```

It prints a JSON summary; read its `diagnostics` (what the package changed or left out, such as the recording, which stays outside) and tell the user. An MML layer opens in keyroam as source text to compile; a MIDI layer carries its readable view's keys and chords. Done when each package is written and its diagnostics are reported.

## 5. Report

Tell the user which scores changed (with `mididiff` PASS), what stayed old and why, the chords written as `X`, and where the packages are.
