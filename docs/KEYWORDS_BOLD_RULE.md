# Keywords marker bold rule

Updated: 2026-03-23

## Rule
- During `normalize_annotation_markers`, the keyword heading marker is always rewritten in bold.
- Applies to normalized headings such as:
  - `Keywords:`
  - `Ключові слова:`

## Implementation
- File: `ядро-реліз-інтегр/core/normalize_annotation_markers.py`
- Mechanism:
  - for each detected keyword marker, paragraph heading is rebuilt via `_replace_paragraph_with_heading(...)`;
  - heading run is explicitly `bold=True`.
