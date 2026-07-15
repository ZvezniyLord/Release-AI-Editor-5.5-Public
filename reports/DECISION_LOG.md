# Decision Log

Date: 2026-07-15

## Decision Entry Format

Every cycle must document decisions with these fields:

- problem
- evidence
- options
- decision
- verification
- status

## 2026-07-15 - Add Decision Playbook

problem:
The public mirror needed an explicit decision-making reference for future journal creation cycles.

evidence:
The cyclic execution plan existed in `docs/CODEX_JOURNAL_FACTORY_CYCLIC_EXECUTION_PLAN.md`, but the public repository did not yet include `docs/JOURNAL_CREATION_DECISION_PLAYBOOK.md` or a cycle decision log.

options:
1. Leave decisions implicit in status reports.
2. Add the playbook and require a structured decision log.

decision:
Add the provided playbook verbatim, include it in the required AGENTS.md reading order, and create `reports/DECISION_LOG.md`.

verification:
The copied playbook SHA256 matches the provided source file.

status:
Done.

## 2026-07-15 - TOC Vertical Slice Contract

problem:
The TOC path allowed unsafe outline interpretation and did not have a deterministic visual contract audit for the Word table layout.

evidence:
`toc_core/outline_parser.py` previously mapped generic Word `Title` / `Title1` to level 1, allowed title rows without authors, and silently created a `Без секції` fallback. The table writer did not fail closed on the required 3-column fixed-width table contract.

options:
1. Patch only the TOC parser/table path and add synthetic artifacts.
2. Regenerate the full private journal pipeline in the public repository.
3. Keep the existing parser behavior and document the risk.

decision:
Patch only TOC code and public synthetic fixtures. Add fail-closed errors `TOC_INPUT_INVALID` and `TOC_VISUAL_CONTRACT_INVALID`, generate synthetic visible artifacts, and keep the journal pipeline, LLM, article processing, and private documents untouched.

verification:
`python -m pytest` passed with 22 tests. `artifacts/toc_vertical_slice/TOC_AUDIT.json` reports PASS with one table, three physical columns, widths 661 / 8170 / 797 twips, central-column text only, three article rows, two journal sections, and one free-listener row.

status:
Done for the public synthetic vertical slice. Private full-journal smoke regeneration remains a known follow-up and is not committed.
