# Evaluate the reconstruction, then the arrangement

For source timing, beat/pitch commands and matched listening excerpts, use [source review](source-review.md). Keep acoustic agreement, reference-note accuracy, listener judgments and piano constraints as separate results.

1. Choose shared excerpts containing lead, dense accompaniment and an instrumental hook. Keep another excerpt out of model/configuration selection. Capture model revision, input hash, source offset, environment lock, elapsed time and RAM/VRAM.
2. Establish recording/reference correspondence independently of candidate note matching. A YouTube edit can omit or reorder sections. Mark unmatched passages; never force a full-song DTW alignment through an edit. All candidates use the same verified mapping.
3. Identify melody/bass roles in each raw candidate from phrase evidence and select its channels consistently. Instrument labels are not authoritative. Compare both the raw selected roles and the curated transcription, documenting the selection so removing everything cannot masquerade as improvement.
4. Use `bash ../piakura-arranger/scripts/tool.sh midieval reference.mid candidate.mid --reference-channels 1 --candidate-channels 1 --alignment alignment.json --json -o evaluation.json`. Read the [metric contract](transcription-evaluation.md) before interpreting it. Onset precision/recall, extra/missing notes, octave diagnostics and duration error answer different questions. The hand-transcribed reference can itself differ from the recording.
5. Review recognizable melody, bass movement, harmonic rhythm, characteristic phrases and spurious notes together. Use the project-authorized CUDA worker for inference; compare model quality and runtime without treating model size as evidence of accuracy. Record failures and unmeasured comparisons explicitly.

For a separately performed piano reference, use [reference comparison](../../piakura-arranger/references/reference-comparison.md) before assigning voice roles or scoring notes.

Keep reference scores out of the input to a blind transcription experiment. If you use them to edit the transcription, identify that run as reference-assisted reconstruction and do not present its improvement as independent model/skill accuracy. Do not transfer notes from an existing piano arrangement and claim they came from audio inference.

After the handoff, `midistat` evaluates piano playability and melody preservation against the curated reference; it is not an AMT accuracy metric. The pre-existing `dist` arrangements are comparison examples, not the unique correct output. Prepare matched excerpts for listening when possible; report whether listening actually occurred.

For an independent skill trial, supply only the skill, its linked tools/docs, a realistic request and the minimum raw artifacts. Keep expected notes and prior correction decisions outside that agent's context. Assess its actual score and reports, not a self-reported PASS. Include a legitimate short/offbeat/chromatic note alongside false positives so a blanket cleanup rule cannot pass.
