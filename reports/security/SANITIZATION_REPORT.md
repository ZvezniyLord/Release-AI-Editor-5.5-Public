# Sanitization Report

Date: 2026-07-15

Result: **PASS** for the sanitized public mirror source tree.

## Source Handling

- The private repository remained private.
- The private repository history was not rewritten.
- The public mirror was built from a new directory without `.git`.

## Removed or Synthetic Files

- `ядро-реліз-інтегр/shapka_core/NameNoName.json`: replaced with synthetic names, `TEST-ORCID`, and invented institutions.
- `docs/audit_103_ny_20260322.md`: replaced with synthetic audit content.
- `ядро-реліз-інтегр/toc_core/docs/outline_detection_report.docx`: omitted from the public mirror.
- `reports/security/PUBLIC_VISIBILITY_BLOCKED.md`: omitted from the public mirror export.
- Private local and network paths in legacy audit notes were replaced with placeholders.
- A private run-path example in `ядро-реліз-інтегр/core/draft_main.py` was replaced with a generic example path.

## Exclusions

- Git history.
- Private DOCX/PDF/ZIP documents and archives.
- Build output, runtime output, logs, caches, local virtual environments, and local secret directories.
- Paid or embedded font files.

## Office Metadata

Allowed Office templates were retained only after metadata cleanup:

- `ядро-реліз-інтегр/assets/templates/Jurnal.dotx`
- `ядро-реліз-інтегр/assets/templates/Table.docx`

Final metadata and security scan results are recorded after the pre-push checks.

## Pre-Push Scan Results

- `gitleaks 8.30.1 dir . --redact`: no leaks found.
- `git grep --cached` high-confidence secret patterns: no matches.
- Staged personal email search: no matches.
- Staged phone search: no matches.
- Numeric ORCID pattern search: no matches.
- ORCID text search: matches only policy text, the imported execution plan, code markers, and `TEST-ORCID`.
- Office/PDF/ZIP inventory: only the two allowed Office templates are present.
- Office metadata inspection: `creator`, `lastModifiedBy`, `Company`, custom properties, comments, revisions, and embedded fonts are clean or absent in retained templates.
