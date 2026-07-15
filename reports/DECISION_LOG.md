# Decision Log

Date: 2026-07-15

## Decision Entry Format

Every cycle must document decisions with these fields:

- problem
- evidence
- options
- decision
- verification
- status

## 2026-07-15 - Add Decision Playbook

problem:
The public mirror needed an explicit decision-making reference for future journal creation cycles.

evidence:
The cyclic execution plan existed in `docs/CODEX_JOURNAL_FACTORY_CYCLIC_EXECUTION_PLAN.md`, but the public repository did not yet include `docs/JOURNAL_CREATION_DECISION_PLAYBOOK.md` or a cycle decision log.

options:
1. Leave decisions implicit in status reports.
2. Add the playbook and require a structured decision log.

decision:
Add the provided playbook verbatim, include it in the required AGENTS.md reading order, and create `reports/DECISION_LOG.md`.

verification:
The copied playbook SHA256 matches the provided source file.

status:
Done.

## 2026-07-15 - TOC Vertical Slice Contract

problem:
The TOC path allowed unsafe outline interpretation and did not have a deterministic visual contract audit for the Word table layout.

evidence:
`toc_core/outline_parser.py` previously mapped generic Word `Title` / `Title1` to level 1, allowed title rows without authors, and silently created a `Без секції` fallback. The table writer did not fail closed on the required 3-column fixed-width table contract.

options:
1. Patch only the TOC parser/table path and add synthetic artifacts.
2. Regenerate the full private journal pipeline in the public repository.
3. Keep the existing parser behavior and document the risk.

decision:
Patch only TOC code and public synthetic fixtures. Add fail-closed errors `TOC_INPUT_INVALID` and `TOC_VISUAL_CONTRACT_INVALID`, generate synthetic visible artifacts, and keep the journal pipeline, LLM, article processing, and private documents untouched.

verification:
`python -m pytest` passed with 22 tests. `artifacts/toc_vertical_slice/TOC_AUDIT.json` reports PASS with one table, three physical columns, widths 661 / 8170 / 797 twips, central-column text only, three article rows, two journal sections, and one free-listener row.

status:
Done for the public synthetic vertical slice. Private full-journal smoke regeneration remains a known follow-up and is not committed.

## 2026-07-15 - Journal 137 Body Before TOC

problem:
TOC was scheduled too early. The journal body must be assembled and reviewed before TOC can safely read final sections, authors, and titles.

evidence:
The Task 1 TOC vertical slice was useful as an isolated core test, but the correct workflow requires article matching, source snapshots, style validation, object fidelity, PDF render, and manual body review before TOC generation.

options:
1. Continue with TOC work immediately.
2. Build a private body-only smoke package from source evidence and ETALON/golden controls, with TOC disabled.
3. Commit private journal artifacts to the public mirror for review.

decision:
Choose option 2. Generate a private BODY_V1 review package without TOC and without `toc_core` changes. Commit only sanitized public reports.

verification:
Private BODY_V1 was generated and rendered to PDF/PNGs. Sanitized metrics: 20 articles, 89 rendered pages, 20 article title starts, 81 canonical style IDs, 11 used final styles, 0 foreign styles, 0 identifier losses. Private pytest passed with 29 tests and 1 warning.

status:
FAIL for review blockers: 1 source-text-loss finding, 1 source-object-loss finding, and 1 near-blank page review finding. Manual review is required. TOC remains disabled.

## 2026-07-15 - Reclassify Golden Baseline And Assemble From Raw Sources

problem:
The prior private `BODY_V1` run used the approved golden journal as the document basis and removed TOC. That validated renderer/auditor behavior, but it did not validate raw article extraction, matching, normalization, style hygiene, object preservation, or ETALON assembly.

evidence:
The previous report recorded that `BODY_V1` came from the approved golden document. The new Task 2.1 requirement explicitly forbids using the golden journal as source or base and allows it only after independent assembly as a read-only comparison reference.

options:
1. Continue treating `BODY_V1` as the journal body assembly.
2. Reclassify it as `GOLDEN_BASELINE_AUDIT` and run a separate raw-source-to-ETALON assembly.
3. Start TOC work before raw-source assembly is stable.

decision:
Choose option 2. Keep the previous artifacts as a baseline auditor check only, then assemble Task 2.1 from raw source article DOCX files into clean ETALON with TOC disabled.

verification:
The Task 2.1 private run reports `assembly_origin = RAW_SOURCE_TO_ETALON`, generated private DOCX/PDF/render artifacts, used the golden journal only for post-assembly comparison, and committed only sanitized public reports. Public mirror pytest passed with 22 tests; private workspace pytest passed with 29 tests and 1 warning.

status:
FAIL for review blockers: one internal article ID remains REVIEW, assembled article count is 19 of 20, and forbidden direct-formatting findings remain. TOC remains disabled.

## 2026-07-15 - Reproducible Assembly Module And A020 Gate

problem:
The Task 2.1 raw-source assembly runner was private and ignored under `build/`, so the public repository contained only sanitized results, not the reproducible assembly logic. A020 also remained REVIEW and blocked 20/20 assembly.

evidence:
Task 2.1 public reports showed `assembly_origin = RAW_SOURCE_TO_ETALON`, but the code for relationship copying, namespace cleanup, dangling style cleanup, internal ID normalization, and provenance generation was not reviewable in public. The A020 private evidence check found author evidence, but not independent title or DOI evidence.

options:
1. Commit private runner as-is, including local paths and conference hardcode.
2. Extract generic assembly modules without private paths/data and add synthetic regression tests.
3. Insert A020 because it is the remaining unused file.

decision:
Choose option 2. Add reusable public modules under `journal_factory/assembly`, synthetic fixtures generated at test time, and regression tests for the Task 2.1 OOXML failures. Do not insert A020 without two independent semantic evidence items.

verification:
Public pytest passed with 25 tests. Private pytest passed with 29 tests and 1 warning. Synthetic raw-source-to-ETALON build passed with 2 matched synthetic articles, 1 synthetic REVIEW case, and 0 missing package relationship targets.

status:
Done for reproducible assembly code and regression coverage. A020 remains REVIEW; V2 was not created. TOC and style cleanup remain blocked.

## 2026-07-15 - LLM-0 Fail-Closed Integration

problem:
The LLM-0 cycle required applying a prepared changeset archive and validating a local Gemma 4 E2B Docker runtime. The archive was not accessible in the workspace, and the configured target model/runtime was not available as an OpenAI-compatible endpoint.

evidence:
The repository was at base `14f64691f925099f84afd9f0b552c68f6353cedd` before edits. The expected `JOURNAL_FACTORY_AI_GOVERNANCE_CHANGESET.zip` was not found in the sandbox attachment mount, Downloads, Desktop, the workspace root, or checked drive roots. Docker Desktop was available. The local Ollama endpoint listed `qwen3.5:latest` and `gemma2:2b`. The local `gemma4-2b-image:latest` returned 404 for `/v1/models` and `/health`.

options:
1. Stop without code changes until the archive and target runtime are supplied.
2. Implement the public governance, Docker, schemas, validators, and synthetic tests from the prompt, but mark the cycle blocked for the missing archive and target runtime.
3. Treat the non-target `gemma2:2b` probe as the target Gemma 4 E2B validation.

decision:
Choose option 2. Add the reproducible public LLM contract code and reports, reject the non-target model as production evidence, and preserve fail-closed blockers.

verification:
Public pytest passed with 32 tests. Docker worker build passed. Worker synthetic smoke passed in mock mode. The non-target `gemma2:2b` probe failed closed on schema validation.

status:
BLOCKED. Do not start A020, style cleanup, journal regeneration, or TOC.

## 2026-07-16 - Align Local LLM Contract With Journal Builder V1

problem:
LLM-0 added useful Docker/client/chunking foundations, but its classifier schema did not match the current journal builder contract. It used a `paragraphs` wrapper and renamed business types such as `empty_paragraph`, `affiliation`, and `main_text`.

evidence:
The LLM-0 schema expected `schema_version`, `prompt_version`, and `paragraphs`. The required contract uses `fragment_status`, `state_update`, `blocks`, `problems`, and `next_action`. The current business contract keeps ORCID under `service_data` in v1.

options:
1. Replace LLM-0 entirely.
2. Preserve LLM-0 foundation and add a versioned `journal_builder` skill with the correct v1 prompt/schema.
3. Promote an ORCID-specific v2 immediately.

decision:
Choose option 2. Preserve Docker/client/chunking code, add authoritative v1 under `skills/journal_builder`, keep v2 as candidate only, and update validators/tests/reports.

verification:
Public pytest passed with 35 tests. Docker worker build passed. Worker image mock smoke passed. Handoff schema validation passed.

status:
Completed. Real Gemma 4 E2B benchmark is explicitly deferred to LLM-0.2.
