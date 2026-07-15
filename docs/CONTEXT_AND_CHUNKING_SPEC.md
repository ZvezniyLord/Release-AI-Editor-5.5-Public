# Context And Chunking Spec

The worker owns chunking.

Rules:

- `model_supported_context` is metadata from the model/runtime.
- `validated_operational_context` is established only by successful benchmark.
- Silent truncation is forbidden.
- Truncate-middle behavior is forbidden.
- Overflow must fail or rechunk.
- Paragraph IDs are stable and must preserve source order.
- Context-only paragraphs may be sent for neighbor evidence, but must not appear
  in model output blocks.
- The model cannot create, delete, duplicate, or reorder paragraph IDs.

Chunk reports must record context, max output, prompt version, schema version,
retry count, rechunk count, latency, tokens/sec when available, and exact ID
valid rate.
