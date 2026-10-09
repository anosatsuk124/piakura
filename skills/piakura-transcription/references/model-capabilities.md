# Public model entry points

Use these primary sources when selecting a backend. The supported commands,
locked revisions and native-score limitations are in [inference](inference.md)
and [candidate evidence](candidate-evidence.md).

- [YourMT3](https://huggingface.co/spaces/mimbres/YourMT3): multi-instrument transcription of mixed recordings.
- [SheetSage2](https://huggingface.co/m-a-p/SheetSage2): vocal/instrumental lead sheets and chord, beat and key proposals. Inspect timestamp drift, register and articulation independently.
- [Basic Pitch](https://github.com/spotify/basic-pitch): instrument/stem transcription with note, onset and contour activations.
- [Demucs](https://github.com/facebookresearch/demucs): derive source estimates from the supplied mixture; separation artifacts remain possible.
- [GAME](https://github.com/openvpi/GAME): singing note-region and boundary proposals.
- [ROSVOT](https://github.com/RickyL-2000/ROSVOT): vocal transcription with RMVPE pitch evidence.
- [Beat This](https://github.com/CPJKU/beat_this): beat/downbeat estimates.
- [MuScriptor](https://huggingface.co/MuScriptor): optional gated transcription models; follow the access conditions in the inference reference.

Capabilities, model confidence and published benchmarks do not establish this
recording's transcription accuracy. Keep pitch, attacks, releases, roles and
harmonic hypotheses reviewable against the supplied audio.
