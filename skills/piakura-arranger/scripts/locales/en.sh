# shellcheck shell=bash
# The delivery README in English; export.sh sources it. Every language
# defines the same msg_ functions (docs/i18n.md).

msg_intro() {
  cat <<'TEXT'
# MIDI for piano

Open a MIDI file to play it or listen to it. The SakuraMML for editing sits next to each MIDI file.
Start with the standard versions; on a small keyboard, choose the 25-key version that suits how you play it.
Each file's report and arrangement plan give its range, transposition, switch points and validation results.

|Version|Easy|Medium|Hard|
|---|---|---|---|
TEXT
}

# msg_link report|plan|review: the name of a score's sidecar link.
msg_link() {
  case "$1" in
  report) printf 'Validation' ;;
  plan) printf 'Plan' ;;
  review) printf 'Voicing exceptions' ;;
  esac
}

# msg_group standard|<range-mode>-<key-policy>: a row of the table.
msg_group() {
  # The backticks are literal Markdown code spans.
  # shellcheck disable=SC2016
  case "$1" in
  standard) printf 'Standard' ;;
  fixed-preserve) printf '25 keys, fixed, original key (`fixed-preserve`)' ;;
  fixed-auto-transpose) printf '25 keys, fixed, transposed (`fixed-auto-transpose`)' ;;
  switch-preserve) printf '25 keys, switching, original key (`switch-preserve`)' ;;
  switch-auto-transpose) printf '25 keys, switching, transposed (`switch-auto-transpose`)' ;;
  esac
}

msg_report_link() { printf 'Arrangement notes, playing conditions and switch table'; }

msg_keyboard_guide() {
  cat <<'TEXT'

## Names in keyboard/ and how to choose

Folder names are `<range-mode>-<key-policy>`.

- `fixed`: the same 25 keys for the whole song, with no OCT switching while playing. Set the keyboard to the target range before you start.
- `switch`: change the instrument's OCT setting section by section. Each change has a rest of at least 2 seconds; follow the switch table in the report.
- `preserve`: keeps the note names of the original key. Octave shifts to fit the range are allowed.
- `auto-transpose`: allows transposing the whole song to fit the range. The transposition is the same for the whole song.

To play in the original key without touching the keyboard during the song, choose `fixed-preserve`; if transposing is fine, `fixed-auto-transpose`.
To also use a lower range in the intro or interludes, choose a `switch` version. Each version's arrangement plan and report give its actual range, transposition and switch points.
TEXT
}

msg_comparisons() { printf 'Listen and compare'; }

# msg_excerpt phrase|harmony|interlude: an excerpt to compare.
msg_excerpt() {
  case "$1" in
  phrase) printf 'Opening melody' ;;
  harmony) printf 'Chord changes' ;;
  interlude) printf 'Instrumental interlude' ;;
  esac
}

msg_playing() {
  cat <<'TEXT'

## Playing and editing

- The 25-key fixed versions use one range for the whole song; the switching versions change range by section. Set up the keyboard with the target MIDI range and the switch rests given in the report.
- After editing an MML file, compile and validate it again. For transposition or switch plans, also update the compiled note IDs.
- A validation PASS means the score meets the defined conditions. Check how it sounds and how it falls under the fingers by listening and playing.

To check the files, run `sha256sum --check SHA256SUMS` in this folder (`shasum -a 256 -c SHA256SUMS` on macOS).
TEXT
}
