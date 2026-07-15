# Known Defects

Date: 2026-07-15

## Open

### ARTICLE_MATCH_AMBIGUOUS

evidence:
Internal article ID `J137-A020` was rechecked in Task 2.2. Semantic author evidence is present, but semantic title evidence is false and semantic DOI evidence is false. It remains REVIEW and was not inserted automatically.

status:
Open. A private `MATCH_REVIEW_PACKET` exists. The editor or deterministic matching rules must resolve this before a complete body can be reviewed as full assembly output.

### ARTICLE_COUNT_MISMATCH

evidence:
The source manifest contains 20 article groups, but Task 2.1/2.2 assembled 19 articles because A020 remains REVIEW.

status:
Open. This remains a FAIL blocker. V2 was not created in Task 2.2.

### FORBIDDEN_DIRECT_FORMATTING

evidence:
The private direct-formatting audit found 1806 forbidden direct-formatting findings in the assembled body. Task 2.2 added an aggregate histogram with 81 rows and 14630 represented direct-formatting findings across allowed/review/forbidden classes.

status:
Open. These must be reviewed and either normalized, explicitly reclassified, or justified by deterministic rules in a later style cleanup cycle. Task 2.2 did not mass-edit formatting.

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
