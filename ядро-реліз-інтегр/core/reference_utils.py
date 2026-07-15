from __future__ import annotations

import json
import re
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
MARKERS_PATH = MODULE_ROOT / "resources" / "markers.json"

DEFAULT_REFERENCE_MARKERS = [
    "Список використаних джерел",
    "Список використаних джерел:",
    "Список літератури:",
    "Список використаної літератури",
    "Література",
    "References",
    "References:",
    "Bibliography",
    "Bibliography:",
    "BIBLIOGRAPHY",
    "List of references",
    "List of reference",
]


def load_reference_markers() -> list[str]:
    try:
        data = json.loads(MARKERS_PATH.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    values = data.get("reference_markers")
    if not isinstance(values, list):
        return DEFAULT_REFERENCE_MARKERS
    cleaned = [str(x).strip() for x in values if str(x).strip()]
    return cleaned or DEFAULT_REFERENCE_MARKERS


def normalize_marker_source(text: str) -> str:
    text = (text or "").replace("\u00a0", " ").lstrip()
    text = re.sub(r"^[Cc](?=писок\b)", "\u0421", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^\s*[IVXLCDM]+\s*[\.\)\-]?\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*\d+\s*[\.\)\-]?\s*", "", text)
    return text


def extract_marker_remainder(text: str, markers: list[str]) -> tuple[str, str | None]:
    source = normalize_marker_source(text)
    lowered = source.casefold()
    cleaned = [m.strip() for m in markers if isinstance(m, str) and m.strip()]
    cleaned.sort(key=len, reverse=True)
    for marker in cleaned:
        m_low = marker.casefold()
        if lowered.startswith(m_low):
            remainder = source[len(marker):]
            remainder = re.sub(r"^[\s\.\:\;\-–—]+", "", remainder)
            return remainder, marker
        marker_base = re.sub(r"[\s\.\:\;\-–—]+$", "", marker)
        if marker_base and lowered.startswith(marker_base.casefold()):
            remainder = source[len(marker_base):]
            remainder = re.sub(r"^[\s\.\:\;\-–—]+", "", remainder)
            return remainder, marker
    return source, None


def matches_reference_marker(text: str, markers: list[str]) -> bool:
    _, marker = extract_marker_remainder(text, markers)
    return marker is not None


def is_cyrillic(text: str) -> bool:
    return bool(re.search(r"[\u0400-\u04FF]", text or ""))


def capitalize_first(text: str) -> str:
    text = text.lstrip()
    if not text:
        return text
    first = text[0]
    if first.isalpha():
        return first.upper() + text[1:]
    return text


def reference_heading(lang: str) -> str:
    return "СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:" if lang == "uk" else "REFERENCES:"
