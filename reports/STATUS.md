# Status

Date: 2026-07-16

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

## Task 2.2 Reproducible Raw Assembly

Task 2.2 made the raw-source assembly logic reproducible in public code without private paths or private data.

Added public assembly modules:

- `journal_factory/assembly/inventory.py`
- `journal_factory/assembly/matcher.py`
- `journal_factory/assembly/snapshot.py`
- `journal_factory/assembly/normalizer.py`
- `journal_factory/assembly/package_importer.py`
- `journal_factory/assembly/provenance.py`
- `journal_factory/assembly/audits.py`
- `journal_factory/assembly/ooxml.py`
- `journal_factory/assembly/synthetic_fixture.py`

Task 2.2 result:

- A020 status: REVIEW.
- A020 automatic insertion: blocked.
- V2 created: no.
- Assembled article count remains: 19.
- Text/object/identifier losses remain: 0 / 0 / 0 for automatically assembled articles.
- Synthetic raw-source-to-ETALON build: PASS.
- Public pytest: PASS, 25 passed.
- Private pytest: PASS, 29 passed, 1 warning.
- Direct-formatting histogram rows: 81.
- Direct-formatting histogram findings: 14630.
- Histogram safe-to-auto-fix findings: 8931.
- Histogram not-safe-to-auto-fix findings: 5699.

Task 2.2 stop condition:

Stop for editor decision on A020. Do not start TOC. Do not start Task 2.3 style cleanup.

## LLM-0 Governance + Docker Local LLM Smoke

Task status: BLOCKED, not production PASS.

Public code added:

- Docker-first local LLM governance document and repo skill.
- JSON Schemas for paragraph classification, model run summary, and handoff.
- `journal_factory.llm` chunking, provider-neutral OpenAI-compatible HTTP client, host runner, schema/ID validators, synthetic fixtures, and public handoff validator.
- Docker worker image and compose topology where source input is mounted only into `journal-worker`; `llm-runtime` receives model weights by read-only mount only.
- Regression tests for invalid JSON, missing/extra/duplicate/reordered IDs, source hash mismatch, overflow rechunk, repeatability, and source-volume isolation.

Verification:

- Public pytest: PASS, 32 passed.
- Docker worker build: PASS.
- Worker image synthetic smoke: PASS in mock mode.
- Local non-target Ollama probe: FAIL-CLOSED because schema contract was not satisfied.

Blockers:

- `CHANGESET_ARCHIVE_UNAVAILABLE`
- `TARGET_GEMMA4_E2B_RUNTIME_NOT_AVAILABLE`
- `GEMMA4_IMAGE_NOT_OPENAI_COMPATIBLE`
- `OLLAMA_GEMMA2_PROBE_SCHEMA_INVALID`
- `GITLEAKS_NOT_INSTALLED`

Stop condition:

Do not start A020, style cleanup, journal regeneration, or TOC.

## LLM-0.1 Contract Alignment And Governance Repair

Task status: COMPLETED.

Base SHA: `5f5adf3b26e73c88dd1ac0cd1ed9969b1f9b2eab`

Implementation SHA: `f78afaa72a7cad0527a295e85a20e980cbc9ee98`

Public changes:

- Added authoritative `skills/journal_builder` with active paragraph classifier v1 prompt/schema and candidate v2 prompt/schema.
- Replaced the previous `paragraphs` output contract with the current `fragment_status`, `state_update`, `blocks`, `problems`, and `next_action` contract.
- Preserved v1 business type names: `empty_paragraph`, `affiliation`, `main_text`, `blocks`, and `service_data`.
- Kept ORCID as `service_data` in v1; v2 candidate may introduce `orcid` only after a migration decision.
- Loaded the system prompt from the versioned skill directory instead of embedding a short English prompt in code.
- Strengthened validation with `jsonschema`, exact ID checks, context-only ID rejection, forbidden response keys, and `MODEL_STATE_DISAGREEMENT`.
- Added missing governance docs for publication/data policy, orchestration, handoff, local LLM integration, context/chunking, multi-chat execution, and roadmap.
- Hardened Docker compose: internal network, no default host port for `llm-runtime`, optional debug binding only to `127.0.0.1`.

Verification:

- Public pytest: PASS, 35 passed.
- Docker worker build: PASS.
- Worker image mock smoke: PASS.
- Handoff validation: PASS.

Closed blockers:

- `CHANGESET_ARCHIVE_UNAVAILABLE`
- `HANDOFF_PLACEHOLDER_SHA`
- `MOCK_AB_TEMPLATE_MISLABEL`
- `V1_CONTRACT_MISMATCH`

Remaining follow-up:

Real Gemma 4 E2B benchmark remains for LLM-0.2. Do not start it without explicit instruction.

## LLM-0.2 Real Gemma Benchmark

Task status: FAILED, not COMPLETED.

Implementation SHA: `fcf857698fe87b642d3464ad6d9ed9719f6ded22`

Public changes:

- Added `journal_factory.llm.benchmark` with versioned fixture loading, JSON Schema response-format support, exact ID/state/semantic gate aggregation, and fail-closed final status rules.
- Added `fixtures/synthetic/llm_benchmark/paragraph_classifier_v1.json`.
- Added regression tests for benchmark gates, mock rejection, endpoint unavailability, context-only IDs, malformed JSON, and state disagreement.
- Kept v1 active and did not promote v2.

Real model result:

- LM Studio `google/gemma-4-e2b` at `http://127.0.0.1:1234`: real benchmark executed, gates failed.
- Host Ollama `gemma4:e2b` at `http://127.0.0.1:11434`: real benchmark executed, gates failed.
- Valid JSON/schema rate: schema failures were 0 for both runtimes.
- Exact ID/state gates failed, so validated operational context remains null.

Verification:

- Public pytest: PASS, 42 passed.
- Docker worker build: PASS.
- Compose config validation: PASS.
- Docker-based gitleaks scan: PASS.

Stop condition:

Stop for review. Do not start LLM-1, prompt repair, A020, style cleanup, journal regeneration, or TOC.

## LLM-0.3 Contract Constrained Repair

Task status: FAILED, not COMPLETED.

Implementation SHA: `6157e6ec930790483f6552c7659dc0632910a14a`

Public changes:

- Added candidate prompt `skills/journal_builder/prompts/paragraph_classifier/v1.1/system.txt`.
- Added candidate input schema `skills/journal_builder/schemas/paragraph_classifier_input.v1_1.schema.json`.
- Kept active v1 prompt and output schema unchanged.
- Added source/context split for v1.1 request payloads.
- Added generated source-ID enum constraints for structured-output schema.
- Added tests for source/context ID separation, context-ID rejection, empty paragraph preservation, state transitions, and benchmark gates.

Real ablation:

- LM Studio `google/gemma-4-e2b`, v1.1: FAILED. Missing source ID `P017` in 3/3 repeats.
- Host Ollama `gemma4:e2b`, v1.1: COMPLETED. Passed all gates in 3/3 repeats.
- Candidate passed one runtime but not both, so promotion is blocked.

Verification:

- Public pytest: PASS, 67 passed.
- Docker worker build: PASS.
- Compose config validation: PASS.
- Docker-based gitleaks scan: PASS.

Stop condition:

Stop for review. Do not promote v1.1, do not start LLM-1, and do not touch journal generation, A020, formatting cleanup, frontmatter, or TOC.
