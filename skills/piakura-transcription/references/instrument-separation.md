# Instrument-specific evidence

Use separation when a particular part remains ambiguous in the mix or in a
broad `other` stem. A four-stem model's `other` can contain guitar, piano and
synthesizers together. Instrument labels describe estimated outputs; they are
not ground-truth tracks or proof of the instrument playing each note.

Compare direct separation of the original mix before separating `other` again:
the second stage can inherit attacks that the first stage already erased. Keep
the original mixture, broad stem, focused stem and residual. A residual is still
an estimate from the supplied mix, not a separately released instrumental.

## Available paths

The existing pinned `demucs` environment supports `htdemucs_6s`, which adds guitar
and piano. The [authors](https://github.com/facebookresearch/demucs) describe the
six-stem model as experimental and warn about piano bleed/artifacts. Its guitar
stem is a useful comparison, not a default replacement for the original mix.

```bash
bash scripts/transcribe.sh setup demucs
# Use the environment path printed by setup:
/PATH/TO/ENV/bin/python -m demucs -n htdemucs_6s -d cpu \
  --segment 7 --shifts 0 --overlap 0.25 --float32 \
  -o "$WORK/separation-six" "$WORK/excerpt/audio.wav"
```

For a focused guitar alternative, the optional `guitar` environment and
`separate_guitar.py` use
[becruily's Mel-Band RoFormer](https://huggingface.co/becruily/mel-band-roformer-guitar)
at revision `6409e7f88754b07ef7ca3bd1b76a15f010f1672a`. The
[owner permits non-commercial use](https://huggingface.co/becruily/mel-band-roformer-guitar/discussions/9);
no formal weight license file is present. Do not describe that permission as a
permissive redistribution license or infer commercial permission. No access
gate or paid service is required for this candidate.

```bash
bash scripts/transcribe.sh setup guitar
/PATH/TO/GUITAR/ENV/bin/python \
  scripts/separate_guitar.py \
  "$WORK/excerpt/audio.wav" "$WORK/guitar-comparison" \
  --model-directory "$RUNTIME/models/guitar" \
  --source-offset 30
```

`$RUNTIME` is the transcription runtime directory (see [inference](inference.md)). Use the actual excerpt offset, or omit `--source-offset` for an untrimmed source.
Output directories must be new. Supply 44.1-kHz stereo and at least ten seconds
with context around the phrase; the wrapper refuses shorter clips because the
upstream loader silently changes its window below ten seconds. It preserves the
sample clock, retains a FLOAT copy of the input, verifies model/config hashes,
and checks output sample count, channel count, rate and finite values. The
manifest records versions, script/lock hashes, source offset, runtime and memory.
These checks establish reproducibility, not note accuracy.

This is an experimental CPU FP32 path with an 11-second effective window and
overlap count 2. GPU behavior has not been established by the CPU integration;
do not assume that a small checkpoint guarantees 8-GB activation memory.

The pinned `audio-separator` 0.47.0 constructor accepts the configuration's
`mlp_expansion_factor=1` but omits forwarding it to the mask estimator, creating
1024-wide hidden layers against 256-wide checkpoint layers. The adapter scopes
that missing argument to model construction and retains strict weight loading.
It does not discard mismatched weights or modify the installed package. This
[implementation detail](https://github.com/nomadkaraoke/python-audio-separator/blob/c7f2a5c8c3beea1f9ec9ab7206caaebc05f45ac4/audio_separator/separator/uvr_lib_v5/roformer/mel_band_roformer.py)
must be rechecked before updating the dependency or model.

## Decide whether a stem helps

1. Compare identical source-clock excerpts, including phrase context. Record any
   resampling, crop offset and playback gain. Do not independently trim silence,
   stretch, or beat-align stems. Independent export normalization can affect
   amplitude comparisons even when sample counts match.
2. Inspect the original and separated transient/spectral evidence around weak
   attacks, same-pitch reattacks, short notes and rests. A sharper or louder
   separated peak is not automatically the original excitation time. Keep
   competing onset and release hypotheses when separation alters the envelope.
3. Run a suitable note candidate backend on a useful stem when needed, using the
   same settings for comparisons. Review missing attacks, invented notes from
   vocal/drum bleed, pitch/octave errors and crop boundaries separately. Agreement
   between models using the same stem is not independent source verification.
4. Apply [rhythm reconstruction](rhythm-reconstruction.md): pulse, subdivisions,
   motif repetitions and voice leading help assess the alternatives. They do not
   justify filling every quiet gap or snapping every expressive note to a grid.
5. Keep roles distinct. An isolated guitar fill can still be arranged as chords,
   a held voicing or silence. More recovered guitar notes do not make them all
   essential melody; use [musical reconstruction](musical-reconstruction.md).

Adopt extra separation only where it resolves an identified ambiguity. Stop if
the added stem merely sounds cleaner without supporting the disputed notes.
Without true isolated reference audio, do not report SDR or numerical source
accuracy from the mixture itself. Preserve failed models and unresolved phrases
in private evidence; review musical quality separately from MIDI validation.
