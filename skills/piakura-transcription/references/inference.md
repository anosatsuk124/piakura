# Inference and reproducibility

`bash scripts/transcribe.sh --help` lists the current interface. The runtime directory holding environments, weights and caches defaults to `PIAKURA_TRANSCRIPTION_RUNTIME` or `$XDG_CACHE_HOME/piakura/transcription` (several GB); use `--runtime /absolute/path` before the subcommand for another location. Each environment is keyed by its full dependency lock hash. Weights and environments are not committed.

Run model inference where the piakura job's transcription settings say: the local commands below on this machine, or the same backends on the user-authorized SSH worker ([GPU worker](gpu-worker.md)). Use the CPU only when the job's device is `cpu` or the user allowed it as the fallback. Derive stems from the supplied mix; run neural separation/evidence with CUDA where the job has a GPU. Local acquisition, conventional signal analysis and rendering need no GPU.

## Audio acquisition

```bash
bash scripts/transcribe.sh ingest 'https://www.youtube.com/watch?v=VIDEO' "$WORK/source"
# Local audio or an excerpt, with source offset recorded:
bash scripts/transcribe.sh ingest "$WORK/source/audio.wav" "$WORK/excerpt" --start 30 --duration 24
```

Output directories must be new. The compressed download and provider metadata are retained; `audio.wav` is 44.1kHz stereo PCM. Inference backends perform their own required resampling. Do not concatenate separately cropped results without restoring offsets and checking note continuity at the joins. If download is rejected, retain the error and use an authorized local input; the helper does not automatically read browser cookies.

## Model selection

Read [public model capabilities](model-capabilities.md) when choosing a backend. For mixed songs compare direct multi-instrument transcription before adding source separation. Basic Pitch is better suited to an isolated instrument/stem. More candidates do not imply their union is a better score.

For a lead-sheet candidate directly from the mix, `sheetsage2` supplies separate
vocal/instrumental melodies, chord/beat/key hypotheses and native token scores.
For phrase-level singing proposals from a derived vocal stem, `review game`
retains note-region and boundary alternatives. Both are optional and require the
specific register/duration review in [candidate evidence](candidate-evidence.md).

### Long-recording clock checks

SheetSage2 generates timestamp tokens as well as notes. A successful export and
plausible beat sequence do not establish alignment with the recording: a long
generation can drift while its early phrases remain accurate. Before adopting
its full-song melody, compare short, independent inferences from early, middle
and late passages on the original audio clock. Use the same source-derived F0
and attack evidence for the whole-recording and excerpt candidates. A lag scan
is a diagnostic hypothesis, not permission to move every note.

When shorter inputs resolve the drift, retain the long output for structure and
make overlapping fresh inferences for the melody. A starting layout is a
16-second ownership core with four seconds of audio context on each side
(24-second interior inputs). Crop the normal mix using `ingest --start ...
--duration ...`, then run the existing local or authorized worker backend on
each crop. These are new generations, not slices of the drifting full output.
Keep each crop's hash, source offset, raw scores and round-trip results.

Add the crop's source offset exactly once. Select notes by their original
attacks inside each ownership core; review notes crossing a join, repeated
attacks, duplicate predictions and voice handoffs with both overlapping views.
Do not re-attack a held note merely because a window begins. Compare overlapping
pitch classes, attacks and releases before choosing one interpretation. Short
inference can still omit notes or choose a different harmony/register; it is
not an automatic accuracy guarantee.

```bash
bash scripts/transcribe.sh setup yourmt3
bash scripts/transcribe.sh infer "$WORK/excerpt/audio.wav" "$WORK/candidate-yourmt3" --model yourmt3
bash scripts/transcribe.sh setup basic-pitch
bash scripts/transcribe.sh infer "$WORK/vocals.wav" "$WORK/candidate-vocals" --model basic-pitch
```

`raw.mid`, `raw.run.json` and logs are saved separately for each attempt. Basic Pitch also retains uncalibrated activation arrays and note events. MuScriptor/YourMT3 outputs do not provide calibrated note confidence. Preserve unknown values rather than substituting velocity or an invented probability.

YourMT3 uses the pinned official Space code/checkpoint, noPS variant, batch size 1, CPU FP32 or GPU FP16 autocast. Upstream code stays in the runtime directory, not in the skill. Its GitHub and Space license labels differ; record the actual artifact source instead of describing everything as Apache-2.0.

MuScriptor is optional: each user must obtain access under its model-specific terms. The gate includes noncommercial restrictions, contact sharing, input/transcription rights representations and indemnity. A noncommercial intention alone does not establish compliance. Do not accept conditions for the user or silently fetch another checkpoint to bypass a gate. Use self-authored/authorized fixtures first; assess any actual song against the accepted conditions. piakura distributes adapters and identifiers, not licensed weights.

Authenticate on the local machine with the account that accepted the model's conditions. Access is granted separately for small and medium. The following CLI supports browser login; do not ask the user to paste tokens into chat:

```bash
mise exec uv@0.12.23 -- uvx --from huggingface-hub==2.1.1 hf auth login
mise exec uv@0.12.23 -- uvx --from huggingface-hub==2.1.1 hf auth whoami
```

The [official authentication guide](https://huggingface.co/docs/huggingface_hub/guides/cli#hf-auth-login) describes the browser flow. Use `mise exec uv@0.12.23 -- uvx --from huggingface-hub==2.1.1 hf` in place of `hf` below when no standalone executable is installed.

After obtaining access, use your own authenticated Hugging Face client to download a pinned checkpoint. For example, `hf download MuScriptor/muscriptor-small model.safetensors --revision 8c127f603b807520fa465c838e9bfee8a91ada4e --local-dir "$WORK/models/muscriptor-small"`. Then:

```bash
bash scripts/transcribe.sh setup muscriptor
bash scripts/transcribe.sh import-weights muscriptor-small "$WORK/models/muscriptor-small/model.safetensors"
bash scripts/transcribe.sh infer "$WORK/fixture/audio.wav" "$WORK/fixture/muscriptor" --model muscriptor-small
# Transfer only weights to an already authorized worker; credentials stay local:
bash scripts/worker.sh --host USER@HOST import-weights muscriptor-small "$WORK/models/muscriptor-small/model.safetensors"
```

Small and medium are supported with pinned revisions and official SHA256 checks. Automatic tempo detection is disabled in this adapter because MuScriptor 0.3 can otherwise move note onsets onto a detected grid; beat correction remains an explicit review step. Large remains a research candidate: it needs more VRAM than the 8 GB GPU the adapter was tested on, so check the worker's free VRAM first. An access grant is not a grant of rights over input music.

## Targeted separation and beats

For an unresolved lead/bass passage, set up `demucs` and run its locked environment's `python -m demucs -n htdemucs --device cpu|cuda --shifts 1 --out <new-assets-directory> <audio>`. Resolve the environment path from setup's JSON output. Compare vocals/bass with the original mix, then run Basic Pitch on the useful stem. If guitar/piano attacks remain mixed in `other`, read [instrument-specific separation](instrument-separation.md) for the six-stem comparison and optional pinned guitar model. The six-stem piano path is not the default because upstream reports artifacts. Keep source separation outside normal CI.

The `audio` environment provides librosa and Beat This for beat/downbeat estimation. Treat beat tracking as evidence, especially at tempo changes and intros. Specify CPU for local work and retain estimated seconds before authoring a score tempo map. Chroma/DTW can propose alignment; phrase/beat anchors still need verification. Use the same verified alignment for all candidates.
