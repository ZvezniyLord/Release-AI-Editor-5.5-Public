# Known Defects

Date: 2026-07-15

## Open

### ARTICLE_MATCH_AMBIGUOUS

evidence:
Internal article ID `J137-A020` did not meet the strict automatic insertion rule requiring independent author and title evidence. It was left in REVIEW and was not inserted automatically.

status:
Open. The editor or deterministic matching rules must resolve this before a complete body can be reviewed as full assembly output.

### ARTICLE_COUNT_MISMATCH

evidence:
The source manifest contains 20 article groups, but Task 2.1 assembled 19 articles because one article remained REVIEW.

status:
Open. This is a Task 2.1 FAIL blocker.

### FORBIDDEN_DIRECT_FORMATTING

evidence:
The private direct-formatting audit found 1806 forbidden direct-formatting findings in the assembled body.

status:
Open. These must be reviewed and either normalized, explicitly reclassified, or justified by deterministic rules.

### Near-blank rendered pages require review

evidence:
The private visual audit flagged 5 near-blank rendered pages in the assembled PDF.

status:
Open. Review whether each page is intentional service/layout behavior or a defect.

### Duplicate paragraph review

evidence:
The private assembled body audit found 63 duplicate paragraph findings by exact sanitized paragraph hash rules.

status:
Open. Requires editor review because repeated references, captions, or boilerplate may be legitimate.

### Manual review required before any PASS

evidence:
Task 2.1 generated a private DOCX/PDF review package, but the editor has not manually approved it.

status:
Open. Full journal PASS remains forbidden.

## Closed Or Superseded

### GOLDEN_BASELINE_AUDIT was not real assembly

status:
Superseded. The prior BODY_V1 run is retained as `GOLDEN_BASELINE_AUDIT`, useful only for renderer/auditor checks. It is not evidence of raw-source extraction, normalization, or ETALON assembly.

### Previous baseline source text/object findings

status:
Superseded for Task 2.1. The raw-source assembly audit reports 0 unknown text loss, 0 unknown object loss, and 0 identifier loss for automatically assembled articles.
