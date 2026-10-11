# Piano output

The standard arrangement layout, `solo`, is TR0 conductor, TR1 right hand, TR2 left hand, both hands on CH1. `split` puts the right hand on CH1 and the left hand on CH2. Even on one channel, keep separate left/right tracks and hand assignments. Also record Right hand/Left hand in the SMF TrackName, and use Voice(1,0,0) for the instrument.

`midistat --piano-mode solo|split` validates the layout. Without it, the channel layout is not validated, for compatibility with the existing CLI. The skill's validate/compare helpers default to solo; a trailing `--piano-mode split` changes it.

In solo, same-pitch overlaps and same-tick handoffs between different tracks are rejected. The same applies when one hand has several tracks. Different SMF tracks have no same-tick execution order shared by all players, so if the NoteOn is sent first, another track's NoteOff may cut it. Leave a release gap of at least 1 tick before a handoff. The validator never shortens notes.

Program, bank, CC, pitch bend and pedal are state shared by the channel. A non-piano program/bank, and conflicting shared settings sent by different tracks on the same tick, FAIL. Use split for separate left/right volume or pedal.

`smf2sakura --no-split-channels` keeps channel changes within an input track. Make the piano solo through the CH settings of the arranged MML.

To audition automatically in Neothesia, set both hands' tracks to Auto. Human waits for the learner's input; Mute does not play. These are independent of the MIDI CH settings. Synthesia also tells left and right apart by separate tracks. [Official guide for content creators](https://synthesiagame.com/support/guide/contentCreators).
