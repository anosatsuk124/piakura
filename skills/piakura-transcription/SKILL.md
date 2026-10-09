---
name: piakura-transcription
description: Transcribe recorded music or repair noisy automatic MIDI transcriptions using audio evidence, musical structure and theory, then hand an editable SakuraMML score to piakura-arranger. Runs model inference on this machine or a user-authorized SSH GPU worker, as the piakura job specifies.
---

# Music transcription

Recover the recognizable melody, bass movement, harmony and characteristic instrumental phrases. Model output is evidence, not an authoritative score. You make musical decisions in SakuraMML; piakura's Go tools parse and analyze MIDI. Difficulty reduction belongs to [piakura-arranger](../piakura-arranger/SKILL.md).

Work inside a piakura job: start from [piakura](../piakura/SKILL.md) if there is none. The job records the user's consent, settings and input, `$WORK` for recordings, real-song MIDI, working scores and private evidence, and `$DELIVERY` for finished copies. Use a new attempt directory under `$WORK` and retain raw outputs. Script paths below are relative to this skill's directory (`scripts/…`) or a sibling skill's (`../piakura-arranger/scripts/…`); run them through that absolute directory. `../piakura-arranger/scripts/tool.sh` runs the installed tools.

Run model inference where the job's transcription settings say: on this machine or on the user-authorized SSH worker ([GPU worker](references/gpu-worker.md)), with its `device`. Retain the job request/result proving the actual backend and device. When CUDA capacity or a CUDA backend is unavailable, follow the job's `gpu_unavailable` choice: wait, stop and report, or use the CPU only if the user allowed it. Local acquisition, non-model signal analysis, SMF processing and rendering need no GPU.

## Establish the recording and evidence

Read [musical reconstruction](references/musical-reconstruction.md) before selecting, deleting, merging or adding notes. Look up the recording's artist, title, version/edit and instrumentation in official sources before interpreting it. Record URLs and separate confirmed metadata, estimates and unknowns. A published key/BPM is a hypothesis until checked against this recording. When only MIDI is supplied, explicitly record the absence of audio evidence and use conservative corrections.

For audio/URL input, read [inference](references/inference.md). Capture source metadata, source hash and any excerpt offset, then run a suitable backend where the job's settings say. For existing model MIDI, start with the next step. Do not require access to a particular gated model to use this skill.

The supplied mixed recording is sufficient input for the workflow. Derive any needed stems from that recording. Separately released instrumental or isolated recordings are optional diagnostic material; keep a reproducible path that cannot access them, including during independent skill trials.

## Reconstruct the score

For audio-derived piano work, read [source review](references/source-review.md) and [rhythm reconstruction](references/rhythm-reconstruction.md) before freezing the handoff. Establish the audio clock, inspect weak or missing attacks, and compare phrase-level rhythms including repeated notes and tuplets; perfect pitch agreement does not verify attack timing. It provides executable beat/pitch evidence and distinguishes source accuracy from arrangement validation.

1. Prepare each raw MIDI with `bash ../piakura-arranger/scripts/prepare.sh raw.mid "$WORK/raw-prepared"`. Both Pretty and Canonical round-trips must pass before editing. A parse/compile failure is a conversion problem, not permission to discard notes. If a model emits an unrepresentable event, retain the raw file and diagnose that boundary explicitly.
2. Read the sidecar and relevant MML, then identify primary melody, bass, harmony, counterlines and percussion. Track/program labels and register are clues; confirm roles across phrases and lead handoffs. Build an evidence note with section boundaries, local beat/key/chord hypotheses and unresolved passages. Treat unknown model confidence as unknown; velocity is not confidence.
3. Create a separate `transcription.mml`. Correct only candidates supported by the evidence hierarchy in the reconstruction reference. For uncertain octaves, overtones, chromatic or missing notes, read [audio evidence](references/audio-evidence.md) and use the candidate-frequency probe with the sidecar's note seconds. Work phrase by phrase with enough surrounding context. Keep coherent note onsets and releases; mark deliberate rhythmic reconstruction and newly inferred notes. Avoid combining all predictions into a larger union of notes.
4. Give the essential tune a dedicated MIDI channel. Review instrumental passages during vocal rests: distinguish a recurring hook or independent melody from an optional fill, slide or chordal texture. Keep replaceable fills on a separate channel; silence in the vocal part does not make every detected instrument a mandatory melody. Identify supported structural sustains and defining short ornaments before assigning optional roles. Check the whole gesture and following arrival; a decoder dropout is not evidence of a breath or an early release. Give bass, harmony and counterlines distinct channels. Reserve CH10 for percussion. Preserve the recording's tempo/form unless the evidence supports a correction. Use `@role`, `@section` and `@source-channel` comments, and cite raw track/event IDs or time ranges for substantive edits in `evidence.md`. Separate transcription corrections from any later arrangement simplification.
5. Compile and inspect revised note data. Compare uncertain passages against audio features, separated stems, motifs or a second model where available. Read [evaluation](references/evaluation.md) when reference MIDI exists or candidate models need comparison. Inspect onset, offset, extra/missing notes and uncertainty separately from model runtime. A better note count or a compiler PASS is not proof of better music.

For tonal ambiguity, chromatic passages, atonal music, noise or percussion-dominant material, reduce harmonic assumptions. Retain supported non-chord tones and unresolved alternatives. Stop repeated inference when another attempt adds no useful evidence; record the remaining limitation instead of inventing a definitive score.

## Handoff and completion

Before freezing the handoff, check bass movement and chord-change timing together with the lead at each distinct texture and role transition. Record the evidence for root, quality and bass separately; empty bass evidence cannot confirm a root-position voicing. Bound unresolved events by time and musical consequence instead of assigning a blanket uncertainty label to the whole harmony.

Write `evidence.md` with the recording/version, role map, corrections and their reasons, unresolved measures and source/model identifiers. Keep tool history in this private file rather than in customer-facing performance notes.

```bash
bash scripts/transcribe.sh handoff "$WORK/transcription.mml" "$WORK/handoff" \
  --melody-channels 1 --evidence "$WORK/evidence.md"
bash scripts/transcribe.sh verify-handoff "$WORK/handoff/handoff.json"
```

The helper compiles the score, verifies both round-trips, checks that selected melody channels have notes and hashes the score, MIDI and evidence. Add `--provisional` if unresolved material remains. This label describes musical review, not an accuracy guarantee. Regenerate the handoff after any edit; do not reuse reports from a previous hash.

If the request includes piano arrangement, continue with `piakura-arranger` using **the verified handoff MIDI** and its melody channels as the preservation reference; it derives a readable reference on the musical clock, so record the beat clock and downbeat evidence in `evidence.md`. Carry uncertainty into the arrangement report. Do not validate melody preservation against uncorrected model output or an unrelated commercial reference MIDI. Use the downstream skill's existing settings, compilation, physical validation and export workflow.

When a human reviewer will listen to or comment on the result, publish the raw candidates, the corrected transcription and any arrangements with [piakura-review](../piakura-review/SKILL.md), and carry the feedback you accept into `evidence.md` before regenerating the handoff.

Finish with editable MML, compiled MIDI, evidence and validation reports, and the requested piano versions. Describe musical limitations that affect playing. A failure or unresolved passage remains visible; never relabel it as a successful transcription solely because the file compiled.
