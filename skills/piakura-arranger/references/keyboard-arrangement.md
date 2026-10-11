# Keyboard size, range and key

The skill takes `keys=N`, `lowest-note=auto|MIDI`, `range-mode=fixed|switch` and `key-policy=preserve|auto-transpose`. Defaults: 88 keys / MIDI 21–108 / fixed / preserve. When 25 keys are given, it proposes the lowest note automatically. The key count is the number of consecutive semitones including black keys; on 25 keys the highest note is the lowest note + 24.

The skill chooses the range for auto and does the arranging. It weighs the melody's contour, octave shifts by whole phrases, the harmony's character, and the hands' layout and semitone clashes while notes are held. For each phrase and harmonic interval, choose register, melody and accompaniment together, and rework the accompaniment's placement/arpeggiation/note count/releases. Details: the skill's [voicing decisions](voicing.md) and [validation contract](voicing-contract.md). Choose the recommended lowest note for the DMK-25 PRO from MIDI Cs (multiples of 12). An explicit lowest note may also be any other note name. If the initial OCT setting is unknown, record the target MIDI range and mark the device's current setting and the number of button presses needed as unconfirmed.

preserve keeps pitch classes and allows the octave shifts needed. auto-transpose chooses one transposition in semitones (-12 to 12) for the whole song. Keep the melody's change from transposition minimal, and keep the same key across all sections.

fixed uses the same N keys for the whole song. switch moves the lowest note per section in steps of 12 semitones. A switch needs both hands released, CC64/66 off, and a rest of a whole number of beats lasting at least 2 seconds. Tempo/time-signature events and all later events also move by the added rest. Put the switch Marker at the start of the rest. With players that do not show Markers, use the report's switch table.

## Validation CLI

To validate a fixed range only:

```bash
bash scripts/tool.sh midistat "$WORK/easy.mid" --profile easy --hands RH=1,LH=2 \
  --piano-mode solo --keys 25 --lowest-note 60 --require-pass
```

To compare octave shifts, transposition and switch rests with the original:

```bash
bash scripts/validate.sh \
  "$WORK/easy.mid" easy "$WORK/easy-report.json" \
  "$WORK/source.mid" 1 --arrangement-plan "$WORK/easy-plan.json"
```

## ArrangementPlan v1

The JSON is at most 16MiB. Unknown fields, multiple JSON values and invalid values are input errors (exit 2). With a plan, its keyboard settings are used, and explicit CLI keys/lowest-note that contradict it are rejected. Record, in order, sections covering the complete source/output timelines. Within a section, no time stretching other than PPQN conversion is allowed.

```json
{
  "version": 1,
  "source_ppqn": 480,
  "output_ppqn": 480,
  "keys": 25,
  "range_mode": "switch",
  "key_policy": "preserve",
  "transpose_semitones": 0,
  "sections": [
    {"name":"section-01","source_start_tick":0,"source_end_tick":960,
     "output_start_tick":0,"output_end_tick":960,"lowest_note":48},
    {"name":"section-02","source_start_tick":960,"source_end_tick":1920,
     "output_start_tick":2880,"output_end_tick":3840,"lowest_note":60}
  ],
  "melody_mapping": [
    {"source":{"track":0,"on_order":10},"output":{"track":1,"on_order":20}},
    {"source":{"track":0,"on_order":12},"omit_reason":"Easy: repeated ornament omitted"}
  ]
}
```

In this example the switch Marker is `Maker("piakura:range:60:84")` at tick 960. The pinned upstream's command name is `Maker` (`Marker` is a syntax error). At 120BPM a 1920-tick rest lasts 2 seconds. Leave in the MML `@section` and `@keyboard-range` for each section, `@octave-switch` at each switch, and `@transpose` at the top.

`melody_mapping` records, for every note of the selected source melody, exactly one output note or omission reason. track/on_order are the SMF's 0-based track and NoteOn event order, taken from the notes of `smf2sakura --no-split-channels --report`. After recompiling the MML, recheck the output IDs.

The validator checks that each output note exists, its onset tick, its pitch class corrected for transposition, and that no output note is assigned to more than one source note. It records the corrected preservation rate as a separate field, and Medium/Hard require 100%. Declare every Easy omission too. Without a reference MIDI, time alignment and key validation are UNKNOWN.

A validation PASS does not guarantee the device's OCT setting, fingering or musical naturalness. The device must be set to the target range before playing.

The skill's standard validation uses `--preserve-melody`: it allows no omissions and also requires held durations preserved under PPQN conversion. ArrangementPlan v1's `omit_reason` can also serve an analysis that explicitly simplifies the melody, but it does not exempt notes from this preservation contract. Matching pitch/onset alone does not let a changed duration pass.
