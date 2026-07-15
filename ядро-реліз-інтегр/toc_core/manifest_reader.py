# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import json


FREE_LISTENER_HEADER_FALLBACK = (
    "SPECIAL THANKS FOR ACTIVE PARTICIPATION IN THE SCIENTIFIC AND PRACTICAL CONFERENCE "
    "ARE EXTENDED TO THE FOLLOWING PARTICIPANTS:"
)


def _load_free_listener_header(sections_path: Path | None) -> str:
    if sections_path is None or not sections_path.exists():
        return FREE_LISTENER_HEADER_FALLBACK
    try:
        data = json.loads(sections_path.read_text(encoding="utf-8"))
    except Exception:
        return FREE_LISTENER_HEADER_FALLBACK
    if not isinstance(data, list):
        return FREE_LISTENER_HEADER_FALLBACK
    for item in data:
        if not isinstance(item, dict):
            continue
        if str(item.get("block_number")) != "0":
            continue
        value = str(item.get("section_en", "") or "").strip()
        if value:
            return value
    return FREE_LISTENER_HEADER_FALLBACK


def load_free_listeners(manifest_path: Path | None) -> tuple[str, list[str]]:
    if manifest_path is None:
        return FREE_LISTENER_HEADER_FALLBACK, []
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        return FREE_LISTENER_HEADER_FALLBACK, []
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return FREE_LISTENER_HEADER_FALLBACK, []
    matches_path = None
    sections_path = None
    if isinstance(raw, dict):
        if raw.get("matches_json_path"):
            matches_path = Path(raw["matches_json_path"])
        if raw.get("sections_path"):
            sections_path = Path(raw["sections_path"])
    header = _load_free_listener_header(sections_path)
    if matches_path is None or not matches_path.exists():
        return header, []
    try:
        raw_matches = json.loads(matches_path.read_text(encoding="utf-8"))
    except Exception:
        return header, []
    if isinstance(raw_matches, dict) and "matches" in raw_matches:
        raw_matches = raw_matches["matches"]
    if not isinstance(raw_matches, list):
        return header, []

    names: list[str] = []
    for item in raw_matches:
        if not isinstance(item, dict):
            continue
        if item.get("match_method") != "free_listener":
            continue
        authors = item.get("authors") or []
        if isinstance(authors, str):
            authors_list = [authors]
        else:
            authors_list = [str(a) for a in authors if str(a).strip()]
        if authors_list:
            names.extend(authors_list)
            continue
        title = (item.get("title") or "").strip()
        if title:
            names.append(title)

    seen = set()
    result: list[str] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        result.append(name)
    return header, result
