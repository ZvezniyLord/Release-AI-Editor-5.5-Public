from __future__ import annotations

import json
from pathlib import Path

from .constants import DEFAULT_STYLE_REGISTRY_PATH

StyleRegistry = dict[str, list[str]]


def load_style_registry(path: Path | None = None) -> StyleRegistry:
    registry_path = path or DEFAULT_STYLE_REGISTRY_PATH
    if not registry_path.exists():
        return {}
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    normalized: StyleRegistry = {}
    for key, value in data.items():
        if not isinstance(key, str):
            continue
        if isinstance(value, list):
            normalized[key] = [str(item) for item in value if str(item).strip()]
    return normalized


def resolve_style_name(document, candidates: list[str]) -> str | None:
    existing = {str(style.NameLocal): str(style.NameLocal) for style in document.Styles}
    normalized = {name.casefold(): name for name in existing}
    for candidate in candidates:
        if candidate in existing:
            return existing[candidate]
        resolved = normalized.get(candidate.casefold())
        if resolved:
            return resolved
    for name in existing:
        folded = name.casefold()
        if any(candidate.casefold() in folded for candidate in candidates):
            return name
    return None


def resolve_from_registry(document, registry: StyleRegistry, key: str) -> str | None:
    candidates = registry.get(key, [])
    if not candidates:
        return None
    return resolve_style_name(document, candidates)
