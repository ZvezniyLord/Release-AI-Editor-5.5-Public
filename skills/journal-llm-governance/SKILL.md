---
name: journal-llm-governance
description: Versioned local LLM governance contract for Journal Factory paragraph classification.
version: 0.1.0
prompt_version: journal-llm-classifier.v1
schema_version: paragraph-classification.v1
---

# Journal LLM Governance

The local model is a reviewer only. It receives JSON chunks and returns JSON
decisions. It never receives source DOCX paths, never reads the filesystem, and
never edits Office documents.

## Runtime Contract

- `journal-worker` reads source packages and creates stable `document_id` and
  `paragraph_id` values.
- `llm-runtime` receives only JSON over an OpenAI-compatible local HTTP API.
- Source volumes are mounted only into `journal-worker`.
- Model weights are mounted read-only into `llm-runtime`.
- `truncate middle` is forbidden; overflow must fail or rechunk.
- JSON Schema validation runs before exact paragraph ID validation.
- Any invalid JSON, missing ID, extra ID, duplicate ID, or reordered ID is
  fail-closed and becomes `REVIEW`, `FAILED`, or `BLOCKED`.

## Required Run Metadata

Every model run report records:

- skill version;
- prompt version;
- schema version;
- git SHA;
- model name and model file SHA-256 when available;
- Docker image name/digest when available;
- model-supported context and validated operational context separately.
