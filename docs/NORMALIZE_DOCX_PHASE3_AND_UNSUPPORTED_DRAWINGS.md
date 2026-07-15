# normalize_docx: phase 3 + unsupported drawings (2026-03-23)

## Phase 3 modularization
- `core/normalize_docx.py` reduced to orchestration-only layer.
- Current file size: ~109 lines.
- Rebuild logic moved to:
  - `core/normalize_docx_parts/rebuild_pipeline.py`

## New unsupported drawing handling (isolated module)
- Added dedicated module:
  - `core/normalize_docx_parts/unsupported_drawing.py`
- Purpose:
  - handle SmartArt/diagram-like blocks that are not regular inline images/charts;
  - avoid changing existing image/chart replacement flow.

## Detection logic
- XML-level detection in:
  - `core/normalize_docx_parts/xml_extract.py`
  - function: `paragraph_unsupported_drawing_count(...)`
- Current trigger:
  - presence of `dgm:relIds` (DrawingML diagram/SmartArt relation marker).

## Runtime behavior
1. During rebuild, each detected unsupported drawing inserts token:
   - `<<UNSUPPORTED_DRAWING_N>>`
2. Post-save COM step tries to copy source floating shape into output.
3. If copy fails, token is replaced with fallback text containing source file path:
   - `[РќР•РџР•Р Р•РќР•РЎР•РќРР™ Р“Р РђР¤Р†Р§РќРР™ Р‘Р›РћРљ: РґРёРІ. РѕСЂРёРіС–РЅР°Р» СЃС‚Р°С‚С‚С– РґР»СЏ СЂСѓС‡РЅРѕРіРѕ РїРµСЂРµРЅРѕСЃСѓ: ...]`
4. Fallback warning formatting:
   - red text (`FF0000`);
   - bold.

## Why this is safe
- Existing chart/image modules remain unchanged.
- Unsupported shape flow is isolated and optional; if no such objects, nothing is added.

## Verified case
- Source:
  - `<PRIVATE_INPUT_ARCHIVE_ROOT>\synthetic_article.docx`
- Result:
  - normalization completes;
  - unsupported smart diagram replaced with fallback marker text if auto-copy is not possible.
