# Handoff And Reporting Protocol

GitHub is the memory between chats. Every completed cycle must commit, push,
return the final remote SHA, and stop.

Each run report must include:

- `SUMMARY.md`;
- `HANDOFF.json`;
- `TEST_RESULTS.md`;
- `ARTIFACT_MANIFEST.json`;
- `DEFECTS.md`;
- `CHECKSUMS.sha256`.

`HANDOFF.json` must validate against `schemas/llm/handoff.schema.json` and must
not contain local absolute paths, secrets, placeholder SHAs, private document
content, or model weights.

Use:

- `base_sha`;
- `implementation_commit_sha`;
- `report_commit_sha`.

Do not require a self-referential SHA inside the same commit. When the report is
committed with the implementation, `report_commit_sha` may be `null`; the final
remote SHA is returned by Codex after push.
