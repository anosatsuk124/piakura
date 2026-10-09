# Candidate-frequency evidence

Use the `probe` helper when an octave, a possible overtone, a chromatic note or a missing note needs checking against audio. It measures supplied frequencies; it does not transcribe audio or decide which notes to change.

```bash
bash scripts/transcribe.sh probe "$WORK/audio.wav" "$WORK/probe-01" \
  --pitches 48,60,72 --windows 2.10:2.30,2.60:2.80
```

Read `probe.json`. The source hash, channel count, time windows and tuning are recorded. Choose windows inside the candidate's sustained portion, then compare onset-adjacent and neighboring windows where useful. The `song.json` emitted by `prepare.sh` provides each note's `start_seconds` and `end_seconds` from the MIDI tempo map. These are MIDI-clock times, not an audio alignment: account for recording/excerpt offsets first. Older sidecars need regeneration to obtain these fields. Tick fields retain the input PPQN, even if MML output scales ticks.

Each window uses a periodic Hann taper after removing each channel's DC mean. Goertzel evaluates each requested frequency; channel powers are averaged before converting to a peak sinusoidal amplitude in dBFS. This preserves anti-phase stereo content that a mono average can cancel. A full-scale sine at an exactly represented frequency is approximately 0 dBFS, a half-scale sine about −6.02 dBFS. `rms_dbfs` measures the unwindowed signal, so a sine's RMS is about 3.01 dB below its peak amplitude. `relative_db` is relative to the strongest **requested candidate in that window**, not to all frequencies or to a probability of correctness. Below −120 dBFS is reported as the numerical floor; all-floor candidates have no relative score.

Interpret several observations together:

- A strong upper octave can be a harmonic of a lower played note. Inspect the fundamental, its neighbors, timing and phrase continuity before adding or deleting a voice. Weak fundamentals also occur in real instruments.
- Nearby simultaneous voices and spectral leakage can support the wrong candidate. Very short windows have poor frequency resolution; `cycles_in_window` below about three is particularly weak evidence. Compare several stable windows rather than a single attack transient.
- Detuning, vibrato and portamento distribute energy around the nominal frequency. Fractional MIDI pitches and `--a4 442` are supported; compare a small neighborhood when the nominal pitch has weak support. Do not retune the score merely to maximize this measurement.
- Silence, a low absolute amplitude or a large relative difference is not calibrated note confidence. A strong candidate can still be another instrument or a harmonic. Record unresolved interpretations and keep theory subordinate to recording evidence.

The command supports 1–128 pitches, 1–32 windows of 0.05–4 seconds each, at most 30 seconds in total, and 1–8 audio channels. It needs `ffmpeg` and `ffprobe`, uses no model weights and refuses existing output directories or intervals extending beyond the audio. It resamples to 44.1 kHz while preserving separate channels.

Method references: [periodic Hann window](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.windows.hann.html), [FFmpeg seeking and output options](https://ffmpeg.org/ffmpeg.html). The implementation is checked against a direct complex DFT and calibrated synthetic audio, including anti-phase stereo and output seeking.
