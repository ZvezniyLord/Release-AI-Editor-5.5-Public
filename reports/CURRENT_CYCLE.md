# Current Cycle

Date: 2026-07-15

Cycle: Task 2.2 - reproducible raw-source assembly and A020 matching gate

Scope:

- Make Task 2.1 raw-source assembly code reproducible in the public repository.
- Preserve existing private V1 artifacts and do not overwrite them.
- Do not generate or insert TOC.
- Do not change `toc_core`.
- Do not begin mass style cleanup.
- Do not commit private DOCX, PDF, source article text, author names, ORCID values, file names, or local paths.

Public code added:

- `journal_factory/assembly/inventory.py`
- `journal_factory/assembly/matcher.py`
- `journal_factory/assembly/snapshot.py`
- `journal_factory/assembly/normalizer.py`
- `journal_factory/assembly/package_importer.py`
- `journal_factory/assembly/provenance.py`
- `journal_factory/assembly/audits.py`
- `journal_factory/assembly/ooxml.py`
- `journal_factory/assembly/synthetic_fixture.py`

Synthetic coverage:

- clean ETALON package generated at test time;
- source articles generated at test time;
- exact author/title match;
- transliterated author match;
- ambiguous match;
- image relationship;
- chart with embedded workbook relationship;
- table;
- equation/drawing;
- duplicated drawing/bookmark IDs;
- source character/table styles;
- `mc:Ignorable` prefix cleanup.

Private A020 matching result:

- A020 status: REVIEW.
- Automatic insertion allowed: no.
- Semantic author evidence: true.
- Semantic title evidence: false.
- Semantic DOI evidence: false.
- V2 created: no.
- Private `MATCH_REVIEW_PACKET` created.

Direct-formatting histogram:

- Histogram rows: 81.
- Total findings represented: 14630.
- Safe-to-auto-fix findings: 8931.
- Not-safe-to-auto-fix findings: 5699.
- Top categories: direct font in body/reference, direct size in reference/body, direct color in references.

Verification:

- Public pytest: PASS, 25 passed.
- Private pytest: PASS, 29 passed, 1 warning.
- Synthetic raw-source-to-ETALON build: PASS, 2 matched synthetic articles and 1 synthetic REVIEW case, 0 missing package relationship targets.

Status:

Stop for editor decision on A020. Do not start TOC and do not start Task 2.3 style cleanup.
