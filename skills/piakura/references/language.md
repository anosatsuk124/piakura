# Language

The job's language is the language people read piakura's output in: `settings.language.value` in `$WORK/piakura-job.json` (outside a job, `bash ../piakura-arranger/scripts/tool.sh piakura config get language`). It is the user's `language` setting or, unset, their locale's language, and `job init` fixes it for the job. Talk to the user in the language of the conversation, which can differ.

Write in the job's language whatever a person reads:

- MML comment prose: notes on phrases, sections and restored deviations, and the reasons after `@gesture` and `@omission`.
- `arrangement-report.md`, `evidence.md`, an arrangement plan's `omit_reason`, a voicing review's `reason`.
- `piakura job note` text, publish messages (`-m`), and the text of a review `spec.json`: `title`, `summary`, layer `label`, section `label`, `note` and `cautions`, annotation `text`, reply `text`.
- Section labels, wherever they appear (`/** @section */` comments, `--sections`, `section_sets`).

Pass it to the tools that write prose: `smf2sakura --mode readable --language CODE` (also through `readable-reference.sh`), `"readable": {"language": "CODE"}` in a review spec, and `export.sh --language CODE` for the delivery README.

Machine-read text keeps its fixed form in every language: tag names and their coded values (`@hand RH`, `@role melody`, `@source-channel 2`), key and chord comments (`/** @key D:maj */`, `/** @chord B:min7 roman=VIm7 */`), note names, MML code, JSON keys and codes, IDs and file names, and the MIDI track names `Right hand` and `Left hand`.
