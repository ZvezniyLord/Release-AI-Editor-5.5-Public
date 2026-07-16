# LLM-0.2 Defects

Status: FAILED

## Open

### REAL_GEMMA_BENCHMARK_GATES_FAILED

evidence:
Real Gemma 4 E2B benchmarks were executed against LM Studio and host Ollama. Both returned JSON that passed the v1 JSON Schema, but neither passed the exact ID/state gates.

status:
Open. LLM-0.2 cannot be marked COMPLETED.

### LMSTUDIO_CONTEXT_ONLY_ID_RETURNED

evidence:
`google/gemma-4-e2b` via LM Studio returned context-only paragraph ID `P018` for both `auto_jinja` and `manual_chatml`.

status:
Open. Exact ID contract rejects context-only IDs.

### LMSTUDIO_AUTO_JINJA_MODEL_STATE_DISAGREEMENT

evidence:
The LM Studio `auto_jinja` run disagreed with deterministic worker state for author status, affiliation, city/country, title, annotation, keywords, body, and references state.

status:
Open.

### OLLAMA_EMPTY_PARAGRAPH_ID_MISSING

evidence:
Host Ollama `gemma4:e2b` omitted decision paragraph ID `P000` in both prompt-template runs.

status:
Open. Exact ID contract rejects missing decision IDs.

### OLLAMA_MODEL_STATE_DISAGREEMENT

evidence:
Host Ollama disagreed with deterministic worker state in both prompt-template runs.

status:
Open.

### DOCKER_MANAGED_GEMMA4_E2B_RUNTIME_NOT_AVAILABLE

evidence:
The Docker Ollama container listed `qwen3.5:latest` and `gemma2:2b`, not Gemma 4 E2B. Real Gemma 4 E2B testing used host LM Studio and host Ollama endpoints bound to localhost.

status:
Open follow-up if future cycles require Docker-managed target model execution rather than host-local endpoints.

## Closed

### REAL_GEMMA4_E2B_BENCHMARK_NOT_RUN

status:
Closed. Real Gemma 4 E2B benchmark requests were executed against local LM Studio and host Ollama endpoints.

### MOCK_NOT_REAL_BENCHMARK

status:
Closed for reporting. Mock is now explicitly rejected as a real benchmark source and is used only for harness smoke.
