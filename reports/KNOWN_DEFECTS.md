# Known Defects

Date: 2026-07-16

## Open

### LLM-0.2 REAL_GEMMA_BENCHMARK_GATES_FAILED

evidence:
Real Gemma 4 E2B benchmarks were executed against LM Studio `google/gemma-4-e2b` and host Ollama `gemma4:e2b`. Both returned v1-schema-valid JSON, but neither passed the exact ID/state gates.

status:
Open. LLM-0.2 is FAILED. Do not start LLM-1 or use the model in journal workflows until this is resolved.

### LLM-0.3 LMSTUDIO_MISSING_AMBIGUOUS_SOURCE_ID_P017

evidence:
Candidate prompt v1.1 with source/context split and source-ID enum constraints still caused LM Studio `google/gemma-4-e2b` to omit source ID `P017` in all 3 repeats.

status:
Open. Candidate v1.1 cannot be promoted.

### LLM-0.2 LMSTUDIO_CONTEXT_ONLY_ID_RETURNED

evidence:
LM Studio returned context-only paragraph ID `P018` for both `auto_jinja` and `manual_chatml`.

status:
Closed for LLM-0.3 candidate v1.1. LM Studio v1.1 had zero context-only ID failures, but still failed on missing `P017`.

### LLM-0.2 OLLAMA_EMPTY_PARAGRAPH_ID_MISSING

evidence:
Host Ollama omitted decision paragraph ID `P000` for both prompt-template runs.

status:
Closed for LLM-0.3 candidate v1.1 on host Ollama. Candidate had zero missing ID failures on Ollama, but overall promotion remains blocked by LM Studio.

### LLM-0.2 MODEL_STATE_DISAGREEMENT

evidence:
LM Studio `auto_jinja` and both host Ollama runs disagreed with deterministic worker state.

status:
Closed for LLM-0.3 candidate v1.1. State failures were zero on both measured runtimes.

### LLM-0 TARGET_GEMMA4_E2B_RUNTIME_NOT_AVAILABLE

evidence:
The required Gemma 4 E2B OpenAI-compatible endpoint/model was not configured. A local Ollama endpoint was available but listed `qwen3.5:latest` and `gemma2:2b`, not Gemma 4 E2B.

status:
Superseded for host-local endpoints by LLM-0.2: LM Studio and host Ollama Gemma 4 E2B endpoints were found and benchmarked. Docker-managed target model availability remains an open follow-up.

### LLM-0 OLLAMA_GEMMA2_PROBE_SCHEMA_INVALID

evidence:
The non-target `gemma2:2b` local probe returned JSON but failed the required schema contract because `schema_version` and `prompt_version` were missing. The response was rejected.

status:
Open. Prompt/runtime tuning belongs to a later LLM cycle.

### ARTICLE_MATCH_AMBIGUOUS

evidence:
Internal article ID `J137-A020` was rechecked in Task 2.2. Semantic author evidence is present, but semantic title evidence is false and semantic DOI evidence is false. It remains REVIEW and was not inserted automatically.

status:
Open. A private `MATCH_REVIEW_PACKET` exists. The editor or deterministic matching rules must resolve this before a complete body can be reviewed as full assembly output.

### ARTICLE_COUNT_MISMATCH

evidence:
The source manifest contains 20 article groups, but Task 2.1/2.2 assembled 19 articles because A020 remains REVIEW.

status:
Open. This remains a FAIL blocker. V2 was not created in Task 2.2.

### FORBIDDEN_DIRECT_FORMATTING

evidence:
The private direct-formatting audit found 1806 forbidden direct-formatting findings in the assembled body. Task 2.2 added an aggregate histogram with 81 rows and 14630 represented direct-formatting findings across allowed/review/forbidden classes.

status:
Open. These must be reviewed and either normalized, explicitly reclassified, or justified by deterministic rules in a later style cleanup cycle. Task 2.2 did not mass-edit formatting.

### Near-blank rendered pages require review

evidence:
The private visual audit flagged 5 near-blank rendered pages in the assembled PDF.

status:
Open. Review whether each page is intentional service/layout behavior or a defect.

### Duplicate paragraph review

evidence:
The private assembled body audit found 63 duplicate paragraph findings by exact sanitized paragraph hash rules.

status:
Open. Requires editor review because repeated references, captions, or boilerplate may be legitimate.

### Manual review required before any PASS

evidence:
Task 2.1 generated a private DOCX/PDF review package, but the editor has not manually approved it.

status:
Open. Full journal PASS remains forbidden.

## Closed Or Superseded

### LLM-0.2 REAL_GEMMA4_E2B_BENCHMARK_NOT_RUN

status:
Closed. Real Gemma 4 E2B benchmark requests were executed in LLM-0.2. The cycle still failed because gates did not pass.

### LLM-0 CHANGESET_ARCHIVE_UNAVAILABLE

status:
Closed in LLM-0.1 as a transfer limitation. The required governance files, prompt/schema contract, handoff protocol, and Docker security changes are now implemented directly in the repository and verified.

### LLM-0 HANDOFF_PLACEHOLDER_SHA

status:
Closed in LLM-0.1. The previous placeholder was removed and the handoff protocol now uses `base_sha`, `implementation_commit_sha`, and `report_commit_sha`.

### LLM-0 V1_CONTRACT_MISMATCH

status:
Closed in LLM-0.1. The active v1 contract now uses `fragment_status`, `state_update`, `blocks`, `problems`, and `next_action` with the required business type names.

### GOLDEN_BASELINE_AUDIT was not real assembly

status:
Superseded. The prior BODY_V1 run is retained as `GOLDEN_BASELINE_AUDIT`, useful only for renderer/auditor checks. It is not evidence of raw-source extraction, normalization, or ETALON assembly.

### Previous baseline source text/object findings

status:
Superseded for Task 2.1. The raw-source assembly audit reports 0 unknown text loss, 0 unknown object loss, and 0 identifier loss for automatically assembled articles.
