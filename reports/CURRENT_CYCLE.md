# Current Cycle

Date: 2026-07-16

Cycle: LLM-0.2 - Real Gemma Benchmark

Scope:

- Add a reproducible benchmark harness for the active journal builder v1 classifier contract.
- Run real local Gemma 4 E2B benchmarks against available OpenAI-compatible endpoints.
- Use versioned synthetic fixtures only.
- Keep v1 active and leave v2 as a candidate.
- Do not change journal assembly, A020, formatting, frontmatter, `toc_core`, or journal DOCX/PDF.

Result:

- Status: FAILED, not COMPLETED.
- Real benchmark executed: yes.
- LM Studio `google/gemma-4-e2b`: FAILED gates because both prompt templates returned context-only ID `P018`; `auto_jinja` also had `MODEL_STATE_DISAGREEMENT`.
- Host Ollama `gemma4:e2b`: FAILED gates because both prompt templates omitted decision ID `P000` and had `MODEL_STATE_DISAGREEMENT`.
- v1 prompt/schema remain active:
  - `skills/journal_builder/prompts/paragraph_classifier/v1/system.txt`
  - `skills/journal_builder/schemas/paragraph_classifier_output.v1.schema.json`

Verification:

- Public pytest: PASS, 42 passed.
- Docker worker build: PASS, `journal-factory-worker:llm0-2`.
- Compose config validation: PASS.
- Mock benchmark smoke: PASS as fail-closed harness check; mock is not accepted as real benchmark.
- Docker-based gitleaks scan: PASS, no leaks found.
- Real Gemma benchmark gates: FAIL.

Stop condition:

Stop after commit and push. Do not start LLM-1, prompt repair, A020, style cleanup, journal regeneration, or TOC.
