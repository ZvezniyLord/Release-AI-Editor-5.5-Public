# order_block: paragraph-limited scope

Updated: 2026-03-23

## Rule
- Front-matter reordering (`UDC -> header -> title`) is limited to the first `N` paragraphs.
- Current limit:
  - `FRONT_SCOPE_MAX_PARAGRAPHS = 45`
  - file: `ядро-реліз-інтегр/core/block_handlers/order_block.py`

## Why
- Some documents do not contain explicit page-break tags, so page-based boundary is unreliable.
- Paragraph cap provides deterministic scope for safe block reordering.

## Affected logic (within capped scope only)
- Title detection.
- UDC detection.
- Header candidate collection.
- Front boundary detection for reordering.

## Report fields
- `scope: "first_n_paragraphs"`
- `scope_max_paragraphs`
- `scope_end_idx`
