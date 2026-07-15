# order_block: title exclusions

Updated: 2026-03-23

## Fix
- In block reordering (`core/block_handlers/order_block.py`), reference headings are now hard-excluded from title detection.

## Excluded from title candidates
- `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ ...`
- `REFERENCES ...`
- `BIBLIOGRAPHY ...`
- Also excludes annotation/keywords/body-start markers during style and fuzzy title matching.

## Result
- Reference block headings no longer get misdetected as article title during front-matter reorder.
