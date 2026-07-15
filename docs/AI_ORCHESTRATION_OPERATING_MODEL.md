# AI Orchestration Operating Model

ChatGPT Lead is the principal architect and reviewer. It sets cycle scope,
reviews evidence, decides when a cycle is accepted, and blocks scope creep.

Codex executes host, model, Word, Docker, integration, test, and GitHub tasks
inside the repository. Codex must commit, push, report, and stop after each
completed cycle.

The local LLM is a classifier/reviewer only. It receives JSON chunks, returns
structured JSON decisions, and cannot read source DOCX paths, access shell or
filesystem tools, edit Office documents, or set production PASS.

Deterministic code remains the production authority for state transitions,
DOCX/OOXML changes, rendering, audits, and release gates.
