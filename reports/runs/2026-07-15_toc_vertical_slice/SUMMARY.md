# Run Summary

Run: `2026-07-15_toc_vertical_slice`

Date: 2026-07-15

Scope: Task 1 - TOC vertical slice only.

## Inputs

- Synthetic source fixture: `fixtures/synthetic/toc/TOC_VERTICAL_SLICE_INPUT.docx`
- Synthetic free-listener manifest: `fixtures/synthetic/toc/manifest.json`
- Synthetic matches fixture: `fixtures/synthetic/toc/matches.json`
- Synthetic free-listener header fixture: `fixtures/synthetic/toc/sections.json`

No private documents, real author records, emails, phones, ORCID values, paid fonts, ZIP archives, or private PDFs were used in committed artifacts.

## Outputs

- `artifacts/toc_vertical_slice/TOC_VERTICAL_SLICE.docx`
- `artifacts/toc_vertical_slice/TOC_VERTICAL_SLICE.pdf`
- `artifacts/toc_vertical_slice/contact_sheet.png`
- `artifacts/toc_vertical_slice/TOC_AUDIT.json`

## Verification

- Full pytest: PASS, 22 passed.
- TOC audit: PASS.
- Contact sheet: visually inspected.
- Synthetic fixture contains the required service `Title` page and an `анкета` noise fragment.
- Generated TOC artifact excludes the `анкета` noise fragment.

## Public Safety Checks

- `gitleaks`: unavailable in the local environment, so no gitleaks PASS is claimed.
- High-confidence secret scan: no matches.
- Email scan: no matches.
- ORCID scan: no matches.
- Phone-like pattern scan: no matches.
- Sensitive file inventory for `.env`, private keys, and archives: no matches.
- DOCX/PDF/ZIP inventory: only the synthetic TOC fixture/output, synthetic TOC PDF, and existing sanitized `Table.docx` template were present.
- Office metadata: synthetic DOCX files use `Synthetic Fixture`; no custom properties, comments, or revisions were found.

## Sanitized Local Smoke Check

Local non-repo `JOURNAL_SMOKE_V2` was checked structurally only.

- private text read or reported: no
- committed to public repository: no
- table count: 3
- first table rows checked: 7
- first table cell counts: 3 cells per checked row
- first table widths: 3213 / 3213 / 3213 twips
- first table central styles: `TABLETEXT`

Result: the existing local smoke artifact appears to be pre-fix or otherwise not representative of the new TOC contract. Regenerate private full-journal smoke separately before production PASS.

## Status

Public synthetic TOC vertical slice: PASS.

Private full-journal smoke regeneration: open follow-up, not committed.
