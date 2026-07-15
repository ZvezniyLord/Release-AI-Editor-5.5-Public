# normalize_docx: modularization phase 2 (2026-03-23)

## What changed
- `core/normalize_docx.py` reduced from ~807 lines to ~331 lines.
- Core helper logic moved into dedicated modules under `core/normalize_docx_parts/`.

## New modules
- `core/normalize_docx_parts/xml_extract.py`
  - DOCX XML parsing helpers.
  - Numbering and rels loaders.
  - Paragraph runs/text/images/charts/textboxes extraction.
- `core/normalize_docx_parts/list_format.py`
  - List format model (`ListFmt`).
  - Roman/alpha conversion.
  - List paragraph detection and prefix generation.
- `core/normalize_docx_parts/table_builder.py`
  - Table border/style/margin setup.
  - Table flattening for nested tables.
  - Template load and output document body preparation.

## normalize_docx.py role after phase 2
- Keeps orchestration only:
  - open source docx
  - iterate body nodes (paragraph/table)
  - apply references/list/media rules
  - save output
  - run COM placeholder replacement

## Compatibility notes
- CLI API unchanged: `normalize_docx.py input --output ...`.
- Fallback imports preserved for both package and script execution modes.
