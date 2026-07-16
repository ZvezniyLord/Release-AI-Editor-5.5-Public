# LLM-0.3 Defects

Status: FAILED

## Open

### LMSTUDIO_MISSING_AMBIGUOUS_SOURCE_ID_P017

evidence:
LM Studio `google/gemma-4-e2b` with candidate v1.1 missed source ID `P017` in all 3 repeats.

status:
Open. Candidate cannot be promoted.

### REAL_GEMMA_BENCHMARK_GATES_FAILED

evidence:
Promotion requires candidate gates to pass on both LM Studio and host Ollama. Host Ollama passed, but LM Studio failed.

status:
Open.

## Closed For Candidate V1.1

### LMSTUDIO_CONTEXT_ONLY_ID_RETURNED

status:
Closed in the measured candidate. LM Studio v1.1 had zero context-only ID failures.

### OLLAMA_EMPTY_PARAGRAPH_ID_MISSING

status:
Closed in the measured candidate. Host Ollama v1.1 had zero missing ID failures.

### MODEL_STATE_DISAGREEMENT

status:
Closed in the measured candidate. v1.1 had zero state failures on both measured runtimes.
