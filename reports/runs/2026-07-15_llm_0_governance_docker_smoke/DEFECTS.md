# Defects

## Open

### CHANGESET_ARCHIVE_UNAVAILABLE

evidence:
The requested archive `JOURNAL_FACTORY_AI_GOVERNANCE_CHANGESET.zip` was not present in the accessible workspace or checked download locations, so its SHA-256 could not be verified and the prepared changeset could not be applied verbatim.

status:
Open. The public code was implemented from the LLM-0 prompt and marked fail-closed.

### TARGET_GEMMA4_E2B_RUNTIME_NOT_AVAILABLE

evidence:
No `LLM_BASE_URL` / `LLM_MODEL` environment was configured for Gemma 4 E2B. The running Ollama endpoint listed `qwen3.5:latest` and `gemma2:2b`, not Gemma 4 E2B.

status:
Open. A validated operational context for Gemma 4 E2B was not established.

### GEMMA4_IMAGE_NOT_OPENAI_COMPATIBLE

evidence:
The local image `gemma4-2b-image:latest` starts, but `/v1/models` and `/health` return 404, so it does not satisfy the provider-neutral OpenAI-compatible runtime contract added in this cycle.

status:
Open.

### OLLAMA_GEMMA2_PROBE_SCHEMA_INVALID

evidence:
The non-target local `gemma2:2b` probe returned JSON, but the response failed schema validation because required `schema_version` and `prompt_version` were missing. The exact paragraph ID valid rate was 0.0.

status:
Open for prompt/runtime tuning in a later LLM cycle. The failure was correctly rejected.

### GITLEAKS_NOT_INSTALLED

evidence:
`gitleaks` is not installed in PATH. `git grep` scans were executed, but the gitleaks portion of the public security scan could not run.

status:
Open.

## Closed

None in this cycle.
