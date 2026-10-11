# Performance delivery contract

`bash scripts/export.sh --language CODE "$WORK" "$DELIVERY"` gathers the performance files from a compiled and validated work directory (`$WORK`) into the delivery directory (`$DELIVERY`). It does not arrange, compile or validate; it lays out the finished files at the destination.

```text
$DELIVERY/
├── README.md                 # delivery README in the job's language: links to each version's MIDI/MML/validation/plan
├── easy.mid / easy.mml       # standard version (Medium/Hard likewise)
├── keyboard/<mode>/          # 25-key fixed/switch × preserve/auto-transpose
├── reports/                 # validation JSON, same layout as the standard version and keyboard/
├── plans/                   # arrangement plan JSON, same layout
├── reviews/                 # optional voicing exception JSON, same layout
├── comparisons/easy/        # phrase/harmony/interlude comparison MIDI and MML
├── report.md                # optional arrangement results, playing conditions, switch table
├── SHA256SUMS
└── .piakura-dist
```

README.md is the delivery README in the job's language: `--language` sets it, defaulting to the piakura `language` setting; its words come from the `locales/` directory beside the script. Each level needs both its MIDI and its MML. Only levels that exist are exported; report/plan/review and comparison files are included when present. The standard version and the four keyboard folders are listed explicitly, so the original, old versions, private arrangement scripts and decisions JSON stay in `$WORK`. report.md is a verbatim copy of `$WORK/arrangement-report.md`, so write its relative links for this delivery layout.

All files are built in a separate directory before the destination is replaced. On failure, such as an incomplete MIDI/MML pair, the previous delivery stays. It rejects input and output paths that are the same or contain each other, a symlink destination, and an existing destination without the ownership marker. Updating an existing delivery folder regenerates it; edits made only in the destination are not carried over.

Verify the delivered contents by running `sha256sum --check SHA256SUMS` in the destination. Keep the delivery out of Git commits. The copy does not re-evaluate validation results or musical judgments.
