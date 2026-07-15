# Known Defects

Date: 2026-07-15

## Open

### Private full-journal smoke artifact not regenerated in public cycle

problem:
The existing local non-repo `JOURNAL_SMOKE_V2` artifact was created outside this public TOC vertical slice and does not show the new TOC table contract in a sanitized structural check.

evidence:
The structural-only check did not read or print private text. It found three tables in the local smoke document. The first table had three columns and seven rows, but grid widths were 3213 / 3213 / 3213 twips and central paragraph style `TABLETEXT`, not the new TOC contract 661 / 8170 / 797 twips with `Tab_SEC`, `Tab_PIP`, and `Tab_Taitl`.

status:
Open. Regenerate and review the private full-journal smoke in a private workspace before claiming production journal PASS. Do not commit private documents or personal data.

## Closed In This Cycle

### Public TOC vertical slice table contract

evidence:
`artifacts/toc_vertical_slice/TOC_AUDIT.json` reports PASS for the synthetic public artifact.

status:
Closed for synthetic vertical slice.
