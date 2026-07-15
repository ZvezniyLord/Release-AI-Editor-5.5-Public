# Initial Repository Audit

Date: 2026-07-15

Source: private repository `ZvezniyLord/Release-AI-Editor-5.5`

Target: sanitized public mirror `ZvezniyLord/Release-AI-Editor-5.5-Public`

## Scope

- Exported current tracked source tree only.
- Did not copy `.git` history.
- Did not copy alternate private branches or tags.
- Removed or replaced files identified as personal-data risks.
- Preserved code files from the tracked source tree, including the dashboard output writer package.

## Public-Visibility Decision

The private source repository was blocked from direct public visibility because personal-data fixtures were present in both the current tree and reachable history.

The public mirror uses a clean history and synthetic replacements instead of rewriting the private repository.

## Files Removed or Replaced

- Replaced `ядро-реліз-інтегр/shapka_core/NameNoName.json` with a synthetic fixture.
- Replaced `docs/audit_103_ny_20260322.md` with a synthetic audit note.
- Omitted `reports/security/PUBLIC_VISIBILITY_BLOCKED.md` from the public mirror export.
- Omitted `ядро-реліз-інтегр/toc_core/docs/outline_detection_report.docx`.
- Omitted all non-template DOCX/PDF/ZIP artifacts found by the export filter.

## Office Templates

Allowed Office templates retained:

- `ядро-реліз-інтегр/assets/templates/Jurnal.dotx`
- `ядро-реліз-інтегр/assets/templates/Table.docx`

Metadata was cleaned before initializing the public Git repository.
