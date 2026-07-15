# Pipeline Updates (2026-03-23)

## What changed
- Dashboard conversion of `.doc/.rtf` now writes converted files into `run_dir/_converted_docx`.
- `matches.json` now stores `working_path` for matched documents.
- `relocate_main.py` now copies from `working_path` first (with fallback to `matched_path`), so normalization no longer reconverts the same `.doc`.
- Launcher UI was simplified:
- Removed manual `convert_mode` selector.
- Removed optional `manifest.json` input field.
- Action buttons are aligned as `3 x 2`.
- Progress parsing in launcher supports more progress markers and updates more reliably.

## Interactive and operator UX
- Candidate confirmation prompt now shows both:
- Dashboard title.
- Candidate text preview snippet.
- Manual add-unknown dialog for authors now uses a larger multiline input.
- For automation, set `AI_EDITOR_ACCEPT_ALL=1` to accept all interactive confirmations.

## Performance and observability
- Added timing output per normalization stage and per file (`normalize_timings.json`).
- Added scan summary timing in dashboard preparation.
- Added Word COM observability controls:
- `WORD_COM_VERBOSE=1` for detailed COM logs.
- `WORD_COM_VISIBLE=1` to make Word window visible during COM operations.
- Conversion cache and reusable Word COM session are enabled in `dashboard_core/io/word_converter.py`.

## Notes from speed test
- Main bottleneck is still content block/header processing, not `.doc` conversion.
- Typical run metrics from test dataset:
- `normalize_folder`: ~142s for 33 files.
- `header_block`: ~83s.
- Conversion overhead was near-zero after relocate consumed `working_path`.
