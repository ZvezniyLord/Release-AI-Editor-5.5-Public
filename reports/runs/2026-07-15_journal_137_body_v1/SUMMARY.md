# Run Summary

Run: `2026-07-15_journal_137_body_v1`

Classification: `GOLDEN_BASELINE_AUDIT`

Date: 2026-07-15

Scope: private golden-baseline auditor/render smoke for journal 137 without TOC.

Important correction:

This run is not evidence of real journal assembly from raw source materials. It used the approved golden journal as the document basis, removed TOC, and checked renderer/auditor behavior. It is retained only as `GOLDEN_BASELINE_AUDIT`.

## Public Safety

- Private source articles, author names, titles, ORCID values, DOCX/PDF artifacts, rendered page images, and local paths are not committed.
- This public report contains only sanitized counts and internal article IDs.
- `toc_core` was not changed.
- TOC was not generated.
- The run must not be treated as raw-source extraction, matching, normalization, or ETALON assembly proof.

## Private Outputs

Generated privately:

- `JOURNAL_137_BODY_V1.docx`
- `JOURNAL_137_BODY_V1.pdf`
- `render_body_v1/*.png`
- `contact_sheet_body_v1.png`
- private article manifest, source snapshots, style registry, and audits

The BODY_V1 document contains the temporary marker `TOC NOT GENERATED IN THIS CYCLE`.

## Metrics

- Status: FAIL.
- Articles: 20.
- Manifest free-listener rows excluded from articles: 7.
- Rendered PDF pages: 89.
- Rendered page PNGs: 89.
- Article title starts detected: 20.
- Manifest section count: 11.
- Final `SECTION` style rows: 10.
- Canonical style registry unique IDs: 81.
- Used final styles: 11.
- Foreign style count: 0.
- Direct formatting warnings: 207.
- Text loss count: 1.
- Object loss count: 1.
- Identifier loss count: 0.
- Near-blank page review count: 1.

## Verification

- Private pytest: PASS, 29 passed, 1 warning.
- Public mirror pytest: PASS, 22 passed.
- PDF render: created.
- Page PNG render: 89 pages created.
- Contact sheet: created.
- Identifier audit: REVIEW, no DOI/ORCID loss.
- Style audit: REVIEW, no foreign styles.
- Fidelity audit: FAIL due source text/object blockers.

## Status

Superseded by Task 2.1 raw-source-to-ETALON assembly. Do not start TOC.
