# Title quote normalization

Updated: 2026-03-23

## Rule
- If detected title text is wrapped with outer quotes, the outer quote pair is removed.

## Supported outer quote pairs
- `" ... "`
- `“ ... ”`
- `« ... »`

## Scope
- Applied in title styling stage (`normalize_titles_docx`) for:
  - matched titles from dashboard data;
  - heuristic title candidates.
