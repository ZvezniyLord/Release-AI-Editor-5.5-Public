# Image preservation in marker normalization

Updated: 2026-03-23

## Problem
- During annotation/reference marker normalization, image-only paragraphs could be treated as empty and removed.

## Fixes
- `core/normalize_annotation_markers.py`
  - Added graphics-aware empty check for paragraph cleanup.
  - Paragraphs with `drawing/pict/object` are not treated as empty.
  - Marker heading replacement skips runs that contain graphics.
- `core/normalize_reference_markers.py`
  - Marker heading replacement skips runs that contain graphics.

## Result
- Images in article body are preserved through marker normalization stages.
