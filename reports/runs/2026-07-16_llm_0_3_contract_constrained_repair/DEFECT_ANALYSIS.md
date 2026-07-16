# LLM-0.3 Defect Analysis

## LMSTUDIO_CONTEXT_ONLY_ID_RETURNED

evidence:
LLM-0.2 LM Studio returned context-only ID `P018` in both prompt-template runs.

change:
Candidate v1.1 separates input into `source_paragraphs` and `context_paragraphs`, explicitly forbids returning context IDs, and generated structured-output schema constrains `blocks[].paragraph_ids` and `problems[].paragraph_ids` to source IDs only.

verification:
LLM-0.3 LM Studio v1.1 had `context_only_id_failures = 0` across 3 repeats.

status:
Closed for the measured candidate.

## OLLAMA_EMPTY_PARAGRAPH_ID_MISSING

evidence:
LLM-0.2 host Ollama omitted source paragraph `P000`, the leading empty paragraph.

change:
Candidate v1.1 explicitly states that empty source paragraphs are full source elements and must be returned once as `empty_paragraph`. Tests cover empty paragraphs at the beginning, middle, end, and consecutive positions.

verification:
LLM-0.3 host Ollama v1.1 had `missing_id_failures = 0` and `valid_output_rate = 1.0` across 3 repeats.

status:
Closed for host Ollama candidate. LM Studio did not miss `P000`, but still missed `P017`.

## MODEL_STATE_DISAGREEMENT

evidence:
LLM-0.2 showed state disagreement in LM Studio `auto_jinja` and both host Ollama runs.

change:
Candidate v1.1 adds an explicit deterministic state algorithm. Validator still computes expected state independently and rejects disagreement.

verification:
LLM-0.3 v1.1 had `state_failures = 0` on both measured runtimes across 3 repeats each.

status:
Closed for the measured candidate.

## LMSTUDIO_MISSING_AMBIGUOUS_SOURCE_ID_P017

evidence:
LLM-0.3 LM Studio v1.1 returned schema-valid JSON and no context-only IDs, but missed source ID `P017` in all 3 repeats.

change attempted:
Candidate v1.1 uses source/context separation, source-ID enum constraints, and explicit exact-ID instructions. No post-inference correction was applied.

verification:
The exact-ID validator rejected all LM Studio v1.1 repeats with `MISSING_ID`.

status:
Open. This keeps the cycle FAILED and blocks prompt promotion.
