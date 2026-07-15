# LLM-0.1 Contract Alignment And Governance Repair

Date: 2026-07-16

Status: COMPLETED

Base SHA: `5f5adf3b26e73c88dd1ac0cd1ed9969b1f9b2eab`

Implementation SHA: `f78afaa72a7cad0527a295e85a20e980cbc9ee98`

Scope:

- Preserve LLM-0 foundation code.
- Add authoritative `skills/journal_builder` prompt/schema contract.
- Align validator with the current `fragment_status/state_update/blocks/problems/next_action` output.
- Add governance docs that were absent when the changeset ZIP was unavailable.
- Tighten Docker runtime exposure so the LLM port is not published by default.
- Do not run a real model benchmark in this cycle.
- Do not change journal assembly, article matching, A020, formatting, frontmatter, `toc_core`, or journal DOCX/PDF.

Contract result:

- Active prompt: `skills/journal_builder/prompts/paragraph_classifier/v1/system.txt`
- Active output schema: `skills/journal_builder/schemas/paragraph_classifier_output.v1.schema.json`
- Candidate v2 prompt/schema added but not activated.
- v1 preserves `empty_paragraph`, `affiliation`, `main_text`, `blocks`, and `service_data`.
- v1 rejects `empty`, `institution`, `body`, `paragraphs`, and ORCID as a separate block type.

Validation result:

- JSON Schema validation now uses `jsonschema`.
- `additionalProperties` is enforced.
- Required fields, enum values, and types are enforced.
- Exact paragraph ID coverage, order, duplicates, missing IDs, extra IDs, and context-only ID leakage are checked.
- `text`, `original_text`, and `block_id` are forbidden in model responses.
- Worker-owned deterministic state is compared against model `state_update`; disagreement fails closed with `MODEL_STATE_DISAGREEMENT`.
- Mock smoke is recorded as transport/schema/ID-contract smoke only, not as model benchmark or prompt-template A/B evidence.

Docker result:

- `llm-runtime` has no source mount.
- Model mount remains read-only.
- Skills are baked into the worker image.
- Development skills mount is read-only.
- Internal Docker network added.
- Default `llm-runtime` publishes no host port.
- Optional debug service binds only `127.0.0.1:${LLM_PORT:-8080}:8080`.

Verification:

- `python -m pytest -q`: PASS, 35 passed.
- Docker worker build: PASS, `journal-factory-worker:llm0-1`.
- Worker image mock smoke: PASS.
- Handoff schema validation: PASS.
- Compose source isolation and network exposure tests: PASS.

Closed blockers:

- `CHANGESET_ARCHIVE_UNAVAILABLE`: closed as transfer limitation; governance files are now implemented and verified directly in the repository.
- `HANDOFF_PLACEHOLDER_SHA`: closed; previous placeholder was replaced with `implementation_commit_sha` and `report_commit_sha: null`.
- `MOCK_AB_TEMPLATE_MISLABEL`: closed; mock is no longer reported as model/template benchmark evidence.
- `V1_CONTRACT_MISMATCH`: closed for public code and schemas.

Open follow-ups:

- Real Gemma 4 E2B OpenAI-compatible benchmark remains for LLM-0.2.
- `GITLEAKS_NOT_INSTALLED` remains a tooling limitation outside this cycle.

Stop condition:

Commit, push, return final remote SHA, and stop. Do not start real model benchmark or LLM-1.
