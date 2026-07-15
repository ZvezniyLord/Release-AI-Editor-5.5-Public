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
- TOC parser now treats `SECTION` as level 1, `AUTOR` as level 2, and `Назва1` as level 3.
- Generic Word `Title` / `Title1` is not treated as a journal section.
- Incomplete author/title pairs fail closed with `TOC_INPUT_INVALID`.
- TOC table output is audited fail-closed with `TOC_VISUAL_CONTRACT_INVALID`.
- Synthetic TOC artifact audit status: PASS.
- Full pytest status: PASS, 22 passed.
- Task 2 private body-only journal 137 smoke was generated without TOC and without `toc_core` changes.
- Task 2 public status: FAIL for review blockers, not PASS.
- Task 2 private body artifact metrics: 20 articles, 89 rendered pages, 20 detected article title starts, 0 foreign styles, 0 identifier losses.
- Task 2 blockers: 1 source-text-loss finding, 1 source-object-loss finding, 1 near-blank page review finding.
- Private DOCX/PDF/render artifacts and private audit JSON were not committed.

Next gate: manual editor review of the private BODY_V1 DOCX/PDF and targeted repair of the source-text and source-object blockers. TOC remains disabled until the journal body is stable.

## Decision Logging Requirement

Every next cycle must document decisions in `reports/DECISION_LOG.md` using this format:

- problem
- evidence
- options
- decision
- verification
- status
