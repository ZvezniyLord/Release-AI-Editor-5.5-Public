# Task 2.2 Reproducible Raw Assembly

Run: `2026-07-15_task_2_2_reproducible_raw_assembly`

Date: 2026-07-15

Status: FAIL, blocked on A020 editor decision.

## Scope

- Preserve private V1 artifacts.
- Move reusable raw-source assembly logic into public code.
- Add synthetic fixtures and regression tests.
- Recheck A020 with independent semantic evidence rules.
- Do not create TOC.
- Do not change `toc_core`.
- Do not begin mass style cleanup.

## Added Public Modules

- `journal_factory/assembly/inventory.py`
- `journal_factory/assembly/matcher.py`
- `journal_factory/assembly/snapshot.py`
- `journal_factory/assembly/normalizer.py`
- `journal_factory/assembly/package_importer.py`
- `journal_factory/assembly/provenance.py`
- `journal_factory/assembly/audits.py`
- `journal_factory/assembly/ooxml.py`
- `journal_factory/assembly/synthetic_fixture.py`

## Synthetic Regression Coverage

- Word-compatible namespace serialization.
- `mc:Ignorable` cleanup.
- Relationship copying only for referenced objects.
- Recursive chart/embedded workbook relationship copying.
- Unique drawing IDs.
- Unique bookmark IDs.
- Dangling `rStyle` removal.
- Dangling `tblStyle` removal.
- No missing package relationship targets.
- Source-to-assembled provenance.
- Exact, transliterated, and ambiguous matching cases.

## Private A020 Result

- A020 status: REVIEW.
- Automatic insertion allowed: no.
- Semantic author evidence: true.
- Semantic title evidence: false.
- Semantic DOI evidence: false.
- V2 created: no.
- Private `MATCH_REVIEW_PACKET` created.

## Assembly Metrics

- V1 preserved: yes.
- V2 created: no.
- Assembled article count remains: 19.
- Title count remains: 19.
- Author block count remains: 19.
- Text loss count: 0.
- Object loss count: 0.
- DOI/UDC/ORCID loss count: 0 / 0 / 0.

## Verification

- Public pytest: PASS, 25 passed.
- Private pytest: PASS, 29 passed, 1 warning.
- Synthetic raw-source-to-ETALON build: PASS.
- Synthetic missing relationship targets: 0.

## Status

Stop for editor decision on A020. Do not start TOC. Do not start Task 2.3 style cleanup.
