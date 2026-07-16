# Current Cycle

Date: 2026-07-16

Cycle: LLM-0.3 - Contract Constrained Repair

Scope:

- Add candidate prompt `paragraph_classifier/v1.1` without changing active v1.
- Separate candidate input into `source_paragraphs` and `context_paragraphs`.
- Add source-ID enum constraints to generated structured-output schema.
- Preserve active v1 business types and keep ORCID as `service_data`.
- Run v1 vs v1.1 ablation on LM Studio and host Ollama, 3 repeats each.
- Do not change journal assembly, A020, formatting, frontmatter, `toc_core`, or journal DOCX/PDF.

Result:

- Status: FAILED, not COMPLETED.
- Host Ollama `gemma4:e2b` with v1.1: COMPLETED gates in all 3 repeats.
- LM Studio `google/gemma-4-e2b` with v1.1: FAILED gates because source ID `P017` was missing in all 3 repeats.
- Candidate v1.1 is not recommended for promotion.
- v1 remains active.

Verification:

- Public pytest: PASS, 67 passed.
- Docker worker build: PASS, `journal-factory-worker:llm0-3`.
- Compose config validation: PASS.
- Mock harness smoke: PASS as fail-closed non-real benchmark.
- Real ablation: executed.
- Docker-based gitleaks scan: PASS, no leaks found.

Stop condition:

Stop after commit and push. Do not start LLM-1, prompt promotion, A020, style cleanup, journal regeneration, or TOC.
