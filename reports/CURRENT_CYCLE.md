# Current Cycle

Date: 2026-07-15

Cycle: Task 1 - TOC vertical slice

Scope:

- TOC parser behavior.
- TOC Word table contract.
- Fail-closed TOC audit.
- Synthetic-only fixtures and visible artifacts.
- Cycle reports.

Out of scope and unchanged:

- LLM behavior.
- Article processing.
- Frontmatter.
- Full journal pipeline.
- Private DOCX/PDF/ZIP inputs and outputs.

Implemented:

- `SECTION` maps to level 1.
- `AUTOR` maps to level 2.
- `Назва1` maps to level 3.
- Generic Word `Title` / `Title1` does not create journal sections.
- Service pages before the first valid section are ignored.
- Title without author and author without title raise `TOC_INPUT_INVALID`.
- Silent `Без секції` fallback was removed.
- TOC table contract now requires three columns and fixed widths 661 / 8170 / 797 twips.
- Article rows contain only two central paragraphs: `Tab_PIP` authors and `Tab_Taitl` title.
- Synthetic audit fails closed with `TOC_VISUAL_CONTRACT_INVALID`.

Verification:

- `python -m pytest`: PASS, 22 passed.
- `artifacts/toc_vertical_slice/TOC_AUDIT.json`: PASS.
- `artifacts/toc_vertical_slice/contact_sheet.png`: visually inspected.
- Local private `JOURNAL_SMOKE_V2` structural check was sanitized and did not read or report private text.

Status:

Public synthetic TOC vertical slice is complete. Private full-journal smoke regeneration remains a follow-up gate.
