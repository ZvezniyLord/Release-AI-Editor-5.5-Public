# LLM-0.2 Real Gemma Benchmark

Date: 2026-07-16

Status: FAILED

Repository: `ZvezniyLord/Release-AI-Editor-5.5-Public`

Base SHA: `932e0bf802de243db1da3399f73cca5371ef4cd4`

Implementation SHA: `fcf857698fe87b642d3464ad6d9ed9719f6ded22`

Scope:

- Add a reproducible LLM-0.2 benchmark harness for the active journal builder v1 contract.
- Run real local Gemma 4 E2B benchmarks against available OpenAI-compatible local endpoints.
- Preserve v1 business types: `empty_paragraph`, `affiliation`, `main_text`, and `service_data`.
- Keep ORCID as `service_data` in v1.
- Do not change journal assembly, A020, formatting, frontmatter, `toc_core`, or journal DOCX/PDF.

Real benchmark execution:

| Runtime | Endpoint | Model | Status | Valid output | Semantic exact | Schema failures | ID failures | Context-only ID failures | State failures | p50 / p95 latency | Tokens/sec |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LM Studio OpenAI-compatible | `http://127.0.0.1:1234` | `google/gemma-4-e2b` | FAILED | 0.0 | 1.0 | 0 | 2 | 2 | 1 | 15159 / 15416 ms | 271.17 |
| Host Ollama OpenAI-compatible | `http://127.0.0.1:11434` | `gemma4:e2b` | FAILED | 0.0 | 0.9444 | 0 | 2 | 0 | 2 | 23868 / 29396 ms | 148.75 |

Gate result:

- `valid_output_rate == 1.0`: FAIL.
- `semantic_exact_rate >= 0.8`: PASS for both runtimes.
- `schema_failures == 0`: PASS.
- `id_contract_failures == 0`: FAIL.
- `context_only_id_failures == 0`: FAIL for LM Studio, PASS for host Ollama.
- `state_failures == 0`: FAIL.

Key findings:

- The real benchmark was run. This is not a mock result.
- LM Studio returned v1-schema-valid JSON and exact semantic labels, but both templates leaked context-only paragraph ID `P018`.
- Host Ollama returned v1-schema-valid JSON, but both templates omitted decision paragraph `P000` and disagreed with deterministic worker state.
- The Docker Ollama container currently does not contain Gemma 4 E2B; the available Gemma 4 E2B endpoints were host LM Studio and host Ollama.
- v1 remains active. v2 remains a candidate and was not promoted.

Verification:

- `python -m pytest -q`: PASS, 42 passed.
- Docker worker build: PASS, `journal-factory-worker:llm0-2`.
- Compose config validation: PASS.
- Mock benchmark smoke: PASS as a fail-closed harness check; mock is not accepted as a real benchmark.
- Docker-based gitleaks scan: PASS, no leaks found.
- Targeted secret/path/email/model-weight scan: PASS after reviewing expected code/test/report matches.

Stop condition:

Stop after commit/push and review. Do not start LLM-1, prompt repair, journal regeneration, A020, formatting cleanup, frontmatter, or TOC.
