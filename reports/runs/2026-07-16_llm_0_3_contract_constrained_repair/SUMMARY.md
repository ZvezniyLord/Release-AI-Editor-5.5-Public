# LLM-0.3 Contract Constrained Repair

Date: 2026-07-16

Status: FAILED

Repository: `ZvezniyLord/Release-AI-Editor-5.5-Public`

Base branch: `agent/llm-0-2-real-gemma-benchmark`

Base SHA: `cdd1132059365a7abaaab69682b9f4fb0e339d22`

Implementation SHA: `6157e6ec930790483f6552c7659dc0632910a14a`

Scope:

- Add candidate prompt `paragraph_classifier/v1.1` without changing active v1.
- Preserve v1 business types: `affiliation`, `main_text`, `empty_paragraph`, and `service_data`.
- Keep ORCID as `service_data` in v1.
- Split candidate input payload into `source_paragraphs` and `context_paragraphs`.
- Add source-ID enum constraints to generated structured-output schema while keeping the stored v1 output schema unchanged.
- Do not post-correct model output after inference.
- Do not change journal assembly, A020, formatting, frontmatter, `toc_core`, DOCX/PDF, or TOC.

Prompt candidate:

- Path: `skills/journal_builder/prompts/paragraph_classifier/v1.1/system.txt`
- SHA-256: `d7d816fe7bb63516ca781fb611638e6d255e93be9ab5bf2b845c619756c7a4c8`
- Output schema: `skills/journal_builder/schemas/paragraph_classifier_output.v1.schema.json`
- Output schema SHA-256: `c7fa809f98bdd1775e58f94f513eb29f761d6b651f029cc988251f949ada665e`

Real ablation:

| Runtime | Prompt | Status | Valid output | Semantic exact | ID failures | Context-only failures | Missing ID failures | Duplicate ID failures | State failures | p50 / p95 latency |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LM Studio `google/gemma-4-e2b` | v1 | FAILED | 0.0 | 0.9630 | 3 | 0 | 0 | 3 | 3 | 13696 / 15934 ms |
| LM Studio `google/gemma-4-e2b` | v1.1 | FAILED | 0.0 | 0.9444 | 3 | 0 | 3 | 0 | 0 | 13865 / 13989 ms |
| Host Ollama `gemma4:e2b` | v1 | FAILED | 0.0 | 0.9444 | 3 | 0 | 3 | 0 | 3 | 17247 / 17792 ms |
| Host Ollama `gemma4:e2b` | v1.1 | COMPLETED | 1.0 | 0.8889 | 0 | 0 | 0 | 0 | 0 | 19088 / 19123 ms |

Decision:

- Do not promote `paragraph_classifier/v1.1`.
- The candidate passed all gates on host Ollama in all 3 repeats.
- The candidate failed all 3 LM Studio repeats because source ID `P017` was missing.
- Since both target runtimes must pass, cycle status is FAILED.

Verification:

- `python -m pytest -q`: PASS, 67 passed.
- Docker worker build: PASS, `journal-factory-worker:llm0-3`.
- Compose config validation: PASS.
- Mock harness smoke: PASS as fail-closed non-real benchmark.
- Real LM Studio ablation: executed, FAILED gates.
- Real host Ollama ablation: executed, v1.1 passed gates.
- Docker-based gitleaks scan: PASS, no leaks found.
- Targeted path/email/secret/model-weight scan: PASS after reviewing expected localhost/date/gitignore/report matches.

Stop condition:

Stop after commit/push and review. Do not start LLM-1, prompt promotion, journal regeneration, A020, formatting cleanup, frontmatter, or TOC.
