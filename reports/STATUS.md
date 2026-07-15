# Status

Date: 2026-07-15

Repository role: sanitized public development mirror.

Default branch: `main`

Current state:

- Private source repository visibility was not changed.
- Private source history was not rewritten.
- Public source tree was created without `.git` history.
- Real author fixture database was replaced with a synthetic fixture.
- Private operational audit was replaced with a synthetic audit note.
- Private DOCX/PDF/ZIP artifacts were not copied.
- Build output, logs, caches, and local secrets were not copied.
- Journal pipeline, LLM, article processing, and DOCX business logic outside TOC were not intentionally changed.
- Task 1 TOC vertical slice is implemented with synthetic-only fixtures and artifacts.
- TOC remains disabled for journal assembly until the journal body is stable and manually reviewed.

## Governance

Every next cycle must document decisions in `reports/DECISION_LOG.md` using this format:

- problem
- evidence
- options
- decision
- verification
- status

## Golden Baseline Audit

The previous private `JOURNAL_137_BODY_V1` run is reclassified as `GOLDEN_BASELINE_AUDIT`.

It was useful for renderer/auditor checks, but it was not a real journal assembly from raw source materials because it used the approved golden journal as the document basis. It must not be treated as evidence that raw article extraction, matching, normalization, style hygiene, or ETALON assembly works.

## Task 2.1 Raw Source To ETALON

assembly_origin = RAW_SOURCE_TO_ETALON

Private raw-source assembly artifacts were generated without TOC and without `toc_core` changes. The approved golden journal was used only after independent assembly as a read-only comparison reference.

Sanitized result:

- Status: FAIL, not PASS.
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
- Rendered page count: 108.
- Near-blank page count: 5.

Verification:

- Public mirror pytest: PASS, 22 passed.
- Private workspace pytest: PASS, 29 passed, 1 warning.
- Private DOCX/PDF/render artifacts and private audit JSON were not committed.

Next gate:

Stop for manual editor review and targeted repair of Task 2.1 blockers. Do not start TOC.
