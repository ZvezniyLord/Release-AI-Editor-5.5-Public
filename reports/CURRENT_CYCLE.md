# Current Cycle

Date: 2026-07-15

Cycle: Task 2.1 - real journal 137 assembly from raw materials

assembly_origin = RAW_SOURCE_TO_ETALON

Scope:

- Build the journal 137 body from raw source article DOCX files and the clean ETALON document.
- Do not generate or insert TOC.
- Do not change `toc_core`.
- Do not use the approved golden journal as a source or assembly base.
- Do not use LLM to edit DOCX.
- Do not commit private DOCX, PDF, source article text, author names, ORCID values, file names, or local paths.

Execution:

- Private conference package inventory and SHA-256 backup were created.
- Article manifest was built from the private workbook/application evidence.
- Strict automatic insertion required independent author evidence and title evidence.
- One internal article ID remained REVIEW and was not inserted automatically.
- Source snapshots were created from OOXML, not only `python-docx` paragraphs.
- Normalized article DOCX packages were created privately.
- The assembled journal body was generated from clean ETALON plus normalized raw-source article content.
- The approved golden journal was used only after assembly for read-only comparison.
- PDF render, page PNG render, and contact sheet were generated privately.

Sanitized results:

- Status: FAIL.
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
- Used final style IDs: `11`, `AUTOR`, `REF-TITLE`, `REFER`, `SECTION`, `TABLETEXT`, `UDC`, `a0`, `af6`, `pip`.
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

Fail conditions:

- `ARTICLE_MATCH_AMBIGUOUS`
- `ARTICLE_COUNT_MISMATCH`
- `FORBIDDEN_DIRECT_FORMATTING`

Verification:

- Public mirror pytest: PASS, 22 passed.
- Private workspace pytest: PASS, 29 passed, 1 warning.

Status:

Stop for manual review and blocker repair. Do not start TOC and do not continue a new architecture cycle.
