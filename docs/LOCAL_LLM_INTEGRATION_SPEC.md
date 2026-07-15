# Local LLM Integration Spec

The local LLM runtime is provider-neutral and must expose an
OpenAI-compatible HTTP API before it can be used for benchmark evidence.

Runtime constraints:

- no hardcoded model filename;
- no hardcoded endpoint;
- model weights mounted read-only;
- source input mounted only into `journal-worker`;
- `llm-runtime` receives JSON only;
- skills and schemas versioned in the repository;
- skills copied into the worker image;
- development skills mount read-only.

Structured output must be validated with the skill JSON Schema first, then with
the exact paragraph ID contract. Invalid JSON, schema errors, missing IDs, extra
IDs, duplicate IDs, reordered IDs, context-only IDs in output, and forbidden
source text fields fail closed.

LLM-0.1 does not run a real model benchmark. Real Gemma 4 E2B benchmarking is a
separate host cycle.
