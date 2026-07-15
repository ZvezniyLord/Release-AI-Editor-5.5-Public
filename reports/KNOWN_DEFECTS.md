# Known Defects

Date: 2026-07-15

## Open

### SOURCE_TEXT_LOSS in private body smoke

evidence:
The private source-to-final audit found 1 missing token in internal article `J137-A007`.

status:
Open. This is a Task 2 FAIL blocker until manually reviewed and repaired or reclassified with evidence.

### SOURCE_OBJECT_LOSS in private body smoke

evidence:
The private object audit found 1 missing media hash in internal article `J137-A012`.

status:
Open. This is a Task 2 FAIL blocker until manually reviewed and repaired or reclassified with evidence.

### Near-blank rendered page requires review

evidence:
The private visual audit flagged 1 near-blank rendered page in the 89-page BODY_V1 PDF.

status:
Open. Review whether it is an intentional service/tail page or a layout defect.

### Manual review required before any PASS

evidence:
Task 2 generated a private DOCX/PDF review package, but the editor has not manually approved it.

status:
Open. Full journal PASS remains forbidden.

## Closed Or Superseded

### Previous full-journal smoke not representative of TOC contract

status:
Superseded by Task 2 body-only private smoke. TOC is intentionally not generated in this cycle.
