from __future__ import annotations

from pathlib import Path
import re

from ..constants import NON_ARTICLE_MARKERS, NON_ARTICLE_TEXT_MARKERS
from .text_utils import canonical, normalize_spaces


ARTICLE_EVIDENCE_MARKERS = tuple(canonical(item) for item in (
    "УДК",
    "UDC",
    "Анотація",
    "Annotation",
    "Abstract",
    "Ключові слова",
    "Keywords",
    "Key words",
))

TEXT_HEADER_SCAN_LINES = 8
SHORT_SERVICE_TEXT_WORD_LIMIT = 80


def _contains_marker(text_key: str, marker_key: str) -> bool:
    if not text_key or not marker_key:
        return False
    return bool(re.search(rf"(?<!\w){re.escape(marker_key)}(?!\w)", text_key))


def is_non_article_filename(path: Path) -> bool:
    filename = canonical(path.name)
    return any(canonical(marker) in filename for marker in NON_ARTICLE_MARKERS)


def is_non_article_text(text: str) -> bool:
    lines = [canonical(line) for line in (text or "").splitlines()]
    lines = [line for line in lines if line]
    normalized = normalize_spaces(" ".join(lines))
    header = normalize_spaces(" ".join(lines[:TEXT_HEADER_SCAN_LINES]))
    marker_keys = [canonical(marker) for marker in NON_ARTICLE_TEXT_MARKERS]
    marker_keys = [marker for marker in marker_keys if marker]

    # Full articles can contain words like "оплата" in the body. Article
    # structure must win over generic service-file markers.
    if any(_contains_marker(normalized, marker) for marker in ARTICLE_EVIDENCE_MARKERS):
        return False

    # Forms usually declare themselves at the top. Restrict marker checks to
    # the header unless the whole document is a short service text.
    if any(_contains_marker(header, marker) for marker in marker_keys if " " in marker):
        return True

    if len(normalized.split()) > SHORT_SERVICE_TEXT_WORD_LIMIT:
        return False

    return any(_contains_marker(header, marker) for marker in marker_keys)
