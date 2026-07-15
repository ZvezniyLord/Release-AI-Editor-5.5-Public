---
name: journal_builder
description: Versioned Journal Factory local LLM prompts and contracts for paragraph classification.
version: 0.1.0
default_prompt: paragraph_classifier/v1
default_output_schema: paragraph_classifier_output.v1
---

# Journal Builder Skill

This skill is the authoritative public contract for local LLM paragraph
classification. The local model is a classifier/reviewer only. It receives JSON
from `journal-worker`, returns JSON, and never edits DOCX files.

## Versions

- `paragraph_classifier/v1`: active contract. Preserves the current business
  type names exactly.
- `paragraph_classifier/v2`: candidate contract only. It is not activated by
  default and requires a migration decision before use.

## Authority

- The worker owns input state and deterministic state transitions.
- The model may return `state_update`, but that update is advisory.
- Any disagreement between model state and deterministic state is recorded as
  `MODEL_STATE_DISAGREEMENT`.
- Invalid JSON, schema failure, missing IDs, extra IDs, duplicate IDs, reordered
  IDs, or context-only IDs in output fail closed.
