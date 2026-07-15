# Privacy and Fixture Policy

This public mirror must contain source code, documentation, and synthetic fixtures only.

## Allowed

- Source code and tests that do not embed real submissions or credentials.
- Synthetic names, synthetic institutions, and placeholder identifiers such as `TEST-ORCID`.
- Office templates after metadata cleanup, when they do not contain private articles, forms, comments, revisions, or embedded paid fonts.

## Not Allowed

- Real articles, applications, author questionnaires, journals, review materials, or archives.
- Real names in fixture databases or operational audit notes.
- Emails, phone numbers, addresses, ORCID identifiers, access tokens, passwords, private keys, `.env` files, or local credentials.
- Build output, runtime logs, caches, local model artifacts, and generated journal output.
- Paid fonts or embedded font files unless license and redistribution rights are documented.

## Fixture Rules

- Use obviously synthetic names such as `Fixture Author Alpha`.
- Use `TEST-ORCID` instead of a real ORCID value.
- Use invented institutions such as `Demo Institute of Public Fixtures`.
- Keep private source material outside this repository.

## Release Gate

Before publishing or pushing to this mirror, run:

- secret scanning;
- personal email and phone search;
- ORCID search;
- Office inventory and metadata inspection;
- filename scan for private document and archive types.
