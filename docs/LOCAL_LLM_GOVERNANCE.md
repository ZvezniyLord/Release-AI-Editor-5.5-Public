# Local LLM Governance

This repository uses a Docker-first local LLM architecture for model-assisted
review. The model is not part of the journal production authority.

Rules:

- `journal-worker` may read source packages and create JSON chunks.
- `llm-runtime` receives JSON only and has no source volume.
- The model does not edit DOCX, set PASS, or access the filesystem.
- Model weights are supplied by an operator-controlled read-only mount and are
  never committed.
- `model_supported_context` and `validated_operational_context` are separate
  fields in reports.
- Context overflow must fail or rechunk. Silent truncation and truncate-middle
  behavior are forbidden.
- JSON Schema validation runs before exact paragraph ID validation.
- Invalid JSON, missing IDs, extra IDs, duplicate IDs, reordered IDs, or source
  text hash changes fail closed.
