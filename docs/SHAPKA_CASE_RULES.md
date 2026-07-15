# Shapka: rules for uppercase/lowercase normalization

## Where operator edits rules
- File: `ядро-реліз-інтегр/resources/markers.json`
- Keys:
  - `titlecase_force_capitalized`
  - `titlecase_force_lowercase`

## Behavior
- `titlecase_force_capitalized`:
  - supports per-language config: `uk` / `en`
  - each language has `phrases` and `words`
  - entries are normalized to canonical capitalized form in header lines (`shapka` pass)
- `titlecase_force_lowercase`:
  - supports per-language config: `uk` / `en`
  - each language has `phrases` and `words`
  - entries are normalized to lowercase form in header lines
  - multi-word phrases are applied before single-word markers to avoid conflicts

## Fallback
- If keys are missing or invalid, defaults are used from `shapka_core/shapka_main.py`.

## Example
```json
"titlecase_force_lowercase": {
  "uk": {
    "phrases": ["кандидат наук", "доктор наук"],
    "words": ["доцент", "професор"]
  },
  "en": {
    "phrases": ["associate professor", "assistant professor"],
    "words": []
  }
}
```
