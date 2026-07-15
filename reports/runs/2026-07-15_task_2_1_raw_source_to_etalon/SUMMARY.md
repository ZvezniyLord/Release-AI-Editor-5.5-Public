# Task 2.1 Raw Source To ETALON Assembly

Run: `2026-07-15_task_2_1_raw_source_to_etalon`

Date: 2026-07-15

assembly_origin = RAW_SOURCE_TO_ETALON

Status: FAIL

## Public Safety

- Private source articles, author names, titles, ORCID values, DOCX/PDF artifacts, rendered page images, and local paths are not committed.
- This public report contains only sanitized counts and internal article IDs.
- `toc_core` was not changed.
- TOC was not generated.
- The approved golden journal was used only after independent assembly as a read-only comparison reference.

## Private Outputs

Generated privately:

- `JOURNAL_137_ASSEMBLED_V1.docx`
- `JOURNAL_137_ASSEMBLED_V1.pdf`
- `render_assembled_v1/*.png`
- `contact_sheet_assembled_v1.png`
- private article manifest, source snapshots, normalized article packages, provenance, style usage, fidelity audits, object audits, identifier audits, and golden comparison

The assembled document contains the temporary marker `TOC NOT GENERATED IN THIS CYCLE`.

## Sanitized Metrics

- Source article count: 20.
- Matched article count: 19.
- REVIEW match count: 1.
- BLOCKED match count: 0.
- Assembled article count: 19.
- Manifest section count: 11.
- Assembled SECTION count: 11.
- Title count: 19.
- Author block count: 19.
- Canonical style count: 74.
- Used final style IDs: 10.
- Foreign style count: 0.
- Allowed direct-formatting count: 705.
- Review direct-formatting count: 10185.
- Forbidden direct-formatting count: 1806.
- Unknown text loss count: 0.
- Unknown object loss count: 0.
- DOI loss count: 0.
- UDC loss count: 0.
- ORCID loss count: 0.
- Duplicate paragraph count: 63.
- Extra non-source text count: 0.
- Rendered PDF pages: 108.
- Rendered page PNGs: 108.
- Near-blank page count: 5.

## Fail Conditions

- `ARTICLE_MATCH_AMBIGUOUS`
- `ARTICLE_COUNT_MISMATCH`
- `FORBIDDEN_DIRECT_FORMATTING`

## Verification

- Public mirror pytest: PASS, 22 passed.
- Private workspace pytest: PASS, 29 passed, 1 warning.
- PDF render: created privately.
- Page PNG render: 108 pages created privately.
- Contact sheet: created privately.
- Identifier audit: 0 DOI loss, 0 UDC loss, 0 ORCID loss.
- Source fidelity audit: 0 unknown text loss and 0 unknown object loss for automatically assembled articles.
- Style audit: 0 foreign styles, but forbidden direct formatting remains.

## Status

Stop for manual editor review and blocker repair. Do not start TOC and do not continue a new architecture cycle.
