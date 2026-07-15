# Defects

## Closed In LLM-0.1

### V1_CONTRACT_MISMATCH

evidence:
LLM-0 used a `paragraphs` wrapper and renamed several business types. LLM-0.1 adds `skills/journal_builder/schemas/paragraph_classifier_output.v1.schema.json` with `fragment_status`, `state_update`, `blocks`, `problems`, and `next_action`.

status:
Closed.

### HANDOFF_PLACEHOLDER_SHA

evidence:
The previous handoff used `PENDING_FINAL_COMMIT_SHA_REPORTED_AFTER_PUSH`. LLM-0.1 replaces it with `implementation_commit_sha` and `report_commit_sha: null`.

status:
Closed.

### MOCK_AB_TEMPLATE_MISLABEL

evidence:
Mock output is now described as transport/schema/ID-contract smoke only. A/B prompt-template comparison is reserved for a real model cycle.

status:
Closed.

### CHANGESET_ARCHIVE_UNAVAILABLE

evidence:
The missing ZIP was a transfer limitation. The required governance files, docs, schemas, prompt, validator, and Docker security changes are now implemented directly in the repository and tested.

status:
Closed for LLM-0.1.

## Open

### REAL_GEMMA4_E2B_BENCHMARK_NOT_RUN

evidence:
Real model benchmark was explicitly out of scope for LLM-0.1.

status:
Open for LLM-0.2.

### GITLEAKS_NOT_INSTALLED

evidence:
This tooling limitation remains from LLM-0. LLM-0.1 uses targeted grep scans and does not claim a gitleaks run.

status:
Open tooling follow-up.
