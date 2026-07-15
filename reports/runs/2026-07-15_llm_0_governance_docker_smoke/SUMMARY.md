# LLM-0 Governance + Docker Local LLM Smoke

Date: 2026-07-15

Status: BLOCKED

Scope:

- Added Docker-first local LLM governance, skill, JSON Schemas, chunking, validators, provider-neutral OpenAI-compatible HTTP client, and host runner.
- Added synthetic-only regression tests for JSON/schema/paragraph ID fail-closed behavior.
- Added Docker worker image and Compose topology where source input is mounted only into `journal-worker`; `llm-runtime` has only a read-only model mount.
- Did not change journal generation, TOC, article matching, or formatting pipeline.

Changeset status:

- Expected archive: `JOURNAL_FACTORY_AI_GOVERNANCE_CHANGESET.zip`
- Expected SHA-256: `1b19f4254aa7763081514925d23892fff53a0a78ae0c295d31a01f4ab51add59`
- Result: archive was not available in the Windows workspace, sandbox attachment mount, Downloads, Desktop, or checked drive roots. The SHA could not be verified and the archive could not be applied.

Verification summary:

- `python -m pytest -q`: PASS, 32 passed.
- Docker Desktop: available.
- Docker worker build: PASS, `journal-factory-worker:llm0`.
- Worker image synthetic smoke: PASS in deterministic mock mode.
- Compose source isolation: PASS by regression test and compose inspection; `llm-runtime` has no source mount.
- Target Gemma 4 E2B OpenAI-compatible runtime: BLOCKED, not available.
- Local `gemma4-2b-image:latest`: starts without source mount, but `/v1/models` and `/health` return 404, so it is not the required OpenAI-compatible runtime.
- Local Ollama OpenAI-compatible probe with `gemma2:2b`: FAIL-CLOSED; JSON parsed, but schema contract failed because required top-level fields were missing.
- Public scan: no actionable secrets or absolute paths found by `git grep`; `gitleaks` is not installed in PATH.

Benchmark table:

| Probe | Model | Template | Context | Threads | Concurrency | Temperature | JSON valid | Exact ID valid | Result |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| mock | synthetic-static-json | auto_jinja | 16384 | 12 | 1 | 0.01 | 1.00 | 1.00 | PASS |
| mock | synthetic-static-json | manual_chatml | 16384 | 12 | 1 | 0.01 | 1.00 | 1.00 | PASS |
| mock | synthetic-static-json | auto_jinja | 8192 | 8 | 1 | 0.10 | 1.00 | 1.00 | PASS |
| mock | synthetic-static-json | auto_jinja | 32768 | 16 | 2 | 0.01 | 1.00 | 1.00 | PASS |
| real-local probe | gemma2:2b | auto_jinja | 8192 | 12 | 1 | 0.01 | 1.00 | 0.00 | FAIL-CLOSED |

Blockers:

- `CHANGESET_ARCHIVE_UNAVAILABLE`
- `TARGET_GEMMA4_E2B_RUNTIME_NOT_AVAILABLE`
- `GEMMA4_IMAGE_NOT_OPENAI_COMPATIBLE`
- `OLLAMA_GEMMA2_PROBE_SCHEMA_INVALID`
- `GITLEAKS_NOT_INSTALLED`

Stop condition:

Stop after commit and push. Do not start A020, style cleanup, journal regeneration, or TOC.
