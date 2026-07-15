# DEPENDENCY_MAP

## Високорівневий граф
`ядро-реліз-інтегр`
→ Word COM (pywin32)
→ python-docx (читання/легкі правки)
→ openpyxl (Excel)
→ локальні ресурси (templates, markers, style_registry).

## Залежності основного ядра (`ядро-реліз-інтегр`)
- `launcher.py` → `dashboard_core.prepare_run` → `core.*` → outputs.
- `core.relocate_main` → `core.relocate_articles` → оновлення `matches.json`.
- `core.normalize_main` → `core.normalize_folder` → `core.normalize_docx`.
- `core.draft_main` → `core.build_draft` → `draft_core.word_draft_builder` → Word COM.
- `core.normalize_authors` / `core.normalize_titles` → python-docx.
- `core.toc_main` → `toc_core.main`.
- `dashboard_core.io.word_converter` → `shared.word_com`.
- `shared.process_cleanup` → `shared.safe_shutdown` → `shared.word_com`.

## TOC‑ядро (`ядро GPT Super Табел`)
- `main.py` → `outline_parser` + `table_builder` + `word_com`.

## Ресурси та артефакти
- `ядро-реліз-інтегр/resources/markers.json` → маркери анотації/ключових/референсів/author‑stop/non‑article.
- `ядро-реліз-інтегр/resources/style_registry.json` → стилі (section/author/title/udc/refer/toc_*).
- `ядро-реліз-інтегр/assets/templates/Jurnal.dotx` → шаблон журналу.
- `ядро-реліз-інтегр/assets/templates/Table.docx` → шаблон таблиці змісту.
- `run_dir/*` → `manifest.json`, `matches.json`, `summary.json`, `dashboard_perevirky.xlsx`, `draft_journal.docx`.
