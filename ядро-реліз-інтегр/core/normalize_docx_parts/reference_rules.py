from __future__ import annotations

import re

HTTP_LINK_RE = re.compile(r"https?://", re.IGNORECASE)
BROKEN_HTTP_LINK_RE = re.compile(r"\b(https?)\s*:\s*/\s*/", re.IGNORECASE)
REF_PREFIX_RE = re.compile(r"(?:url|doi|dio)\s*:\s*$", re.IGNORECASE)
REF_PREFIX_SOFT_RE = re.compile(r"(url|doi|dio)\s*:?\s*$", re.IGNORECASE)
REF_TEXT_NUMBERING_RE = re.compile(r"^\s*\d{1,3}(?:\s*[\.\)\-]\s*|\s+)(?=[^\d\s])")


def _reference_http_prefix(text: str) -> tuple[int | None, int, str]:
    source = (text or "").strip()
    if not source:
        return None, 0, ""
    match = HTTP_LINK_RE.search(source)
    if not match:
        return None, 0, ""
    url_start = match.start()
    before_http = source[:url_start]
    soft = REF_PREFIX_SOFT_RE.search(before_http)
    if soft:
        token = (soft.group(1) or "").lower()
        normalized = "DOI: " if token in {"doi", "dio"} else "URL: "
        if REF_PREFIX_RE.search(before_http):
            return None, 0, ""
        return soft.start(), url_start - soft.start(), normalized
    tail = source[url_start:].lower()
    prefix = "DOI: " if "doi.org" in tail else "URL: "
    return url_start, 0, prefix


def _reference_text_numbering_prefix(text: str) -> tuple[int | None, int]:
    source = text or ""
    match = REF_TEXT_NUMBERING_RE.match(source)
    if not match:
        return None, 0
    return match.start(), match.end() - match.start()


def _fix_url_protocol_spacing(
    line: list[tuple[str, bool, bool, bool, bool]]
) -> list[tuple[str, bool, bool, bool, bool]]:
    plain = "".join(text for text, _, _, _, _ in line)
    matches = list(BROKEN_HTTP_LINK_RE.finditer(plain))
    if not matches:
        return line
    for match in reversed(matches):
        replacement = f"{match.group(1).lower()}://"
        line = _remove_range_in_line_runs(line, match.start(), match.end() - match.start())
        line = _insert_text_in_line_runs(line, match.start(), replacement)
    return line


def _insert_text_in_line_runs(
    line: list[tuple[str, bool, bool, bool, bool]],
    offset: int,
    insert_text: str,
) -> list[tuple[str, bool, bool, bool, bool]]:
    if not insert_text:
        return line
    if not line:
        return [(insert_text, False, False, False, False)]
    if offset <= 0:
        first_bold, first_italic, first_superscript, first_subscript = line[0][1], line[0][2], line[0][3], line[0][4]
        return [(insert_text, first_bold, first_italic, first_superscript, first_subscript), *line]

    out: list[tuple[str, bool, bool, bool, bool]] = []
    pos = 0
    inserted = False
    for text, bold, italic, superscript, subscript in line:
        seg_len = len(text)
        if not inserted and offset <= pos + seg_len:
            split_at = max(0, min(seg_len, offset - pos))
            left = text[:split_at]
            right = text[split_at:]
            if left:
                out.append((left, bold, italic, superscript, subscript))
            out.append((insert_text, bold, italic, superscript, subscript))
            if right:
                out.append((right, bold, italic, superscript, subscript))
            inserted = True
        else:
            out.append((text, bold, italic, superscript, subscript))
        pos += seg_len
    if not inserted:
        last_bold, last_italic, last_superscript, last_subscript = line[-1][1], line[-1][2], line[-1][3], line[-1][4]
        out.append((insert_text, last_bold, last_italic, last_superscript, last_subscript))
    return out


def _remove_range_in_line_runs(
    line: list[tuple[str, bool, bool, bool, bool]],
    start: int,
    length: int,
) -> list[tuple[str, bool, bool, bool, bool]]:
    if length <= 0:
        return line
    end = start + length
    out: list[tuple[str, bool, bool, bool, bool]] = []
    pos = 0
    for text, bold, italic, superscript, subscript in line:
        seg_start = pos
        seg_end = pos + len(text)
        if seg_end <= start or seg_start >= end:
            out.append((text, bold, italic, superscript, subscript))
        else:
            left_cut = max(0, start - seg_start)
            right_cut = max(0, seg_end - end)
            if left_cut > 0:
                out.append((text[:left_cut], bold, italic, superscript, subscript))
            if right_cut > 0:
                out.append((text[-right_cut:], bold, italic, superscript, subscript))
        pos = seg_end
    return out


def normalize_reference_line_runs(
    line: list[tuple[str, bool, bool, bool, bool]]
) -> list[tuple[str, bool, bool, bool, bool]]:
    plain = "".join(text for text, _, _, _, _ in line)
    num_start, num_len = _reference_text_numbering_prefix(plain)
    if num_start is not None and num_len > 0:
        line = _remove_range_in_line_runs(line, num_start, num_len)
        plain = "".join(text for text, _, _, _, _ in line)
    line = _fix_url_protocol_spacing(line)
    plain = "".join(text for text, _, _, _, _ in line)
    insert_at, remove_len, prefix = _reference_http_prefix(plain)
    if insert_at is None or not prefix:
        return line
    if remove_len > 0:
        line = _remove_range_in_line_runs(line, insert_at, remove_len)
    return _insert_text_in_line_runs(line, insert_at, prefix)
