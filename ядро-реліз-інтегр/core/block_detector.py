from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from docx import Document

MODULE_ROOT = Path(__file__).resolve().parents[1]
MARKERS_PATH = MODULE_ROOT / "resources" / "markers.json"

UDC_RE = re.compile(r"^\s*(\u0423\u0414\u041a|UDC|UDK)\b", re.IGNORECASE)


@dataclass(frozen=True)
class ArticleBlocks:
    udc_line: int | None
    title_line: int | None
    annotation_line: int | None
    keywords_line: int | None
    references_line: int | None
    header_range: tuple[int, int] | None


def _load_markers() -> dict:
    try:
        data = json.loads(MARKERS_PATH.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    return data


def _list_markers(data: dict, key: str, fallback: list[str]) -> list[str]:
    raw = data.get(key)
    if not isinstance(raw, list):
        return fallback
    cleaned = [str(x).strip() for x in raw if str(x).strip()]
    return cleaned or fallback


def _is_marker_hit(text: str, markers: list[str]) -> bool:
    low = (text or "").strip().lower()
    if not low:
        return False
    for marker in markers:
        m = marker.strip().lower()
        if not m:
            continue
        if low.startswith(m):
            return True
        m_base = re.sub(r"[\s\.\:\;\-]+$", "", m)
        if m_base and low.startswith(m_base):
            return True
    return False


def detect_article_blocks(doc_path: Path) -> ArticleBlocks:
    data = _load_markers()
    annotation_markers = _list_markers(data, "annotation_markers", ["\u0410\u043d\u043e\u0442\u0430\u0446\u0456\u044f", "Annotation", "Abstract"])
    keyword_markers = _list_markers(data, "keyword_markers", ["\u041a\u043b\u044e\u0447\u043e\u0432\u0456 \u0441\u043b\u043e\u0432\u0430", "Keywords", "Key words"])
    reference_markers = _list_markers(
        data,
        "reference_markers",
        ["\u0421\u043f\u0438\u0441\u043e\u043a \u0432\u0438\u043a\u043e\u0440\u0438\u0441\u0442\u0430\u043d\u0438\u0445 \u0434\u0436\u0435\u0440\u0435\u043b", "References", "List of references"],
    )

    doc = Document(doc_path)
    udc_line = None
    title_line = None
    annotation_line = None
    keywords_line = None
    references_line = None

    first_non_empty = None
    for idx, para in enumerate(doc.paragraphs, start=1):
        text = (para.text or "").strip()
        if not text:
            continue
        if first_non_empty is None:
            first_non_empty = idx
        if udc_line is None and UDC_RE.search(text):
            udc_line = idx
        if annotation_line is None and _is_marker_hit(text, annotation_markers):
            annotation_line = idx
        if keywords_line is None and _is_marker_hit(text, keyword_markers):
            keywords_line = idx
        if references_line is None and _is_marker_hit(text, reference_markers):
            references_line = idx

    if udc_line is not None:
        title_start = udc_line + 1
    elif first_non_empty is not None:
        title_start = first_non_empty + 1
    else:
        title_start = None

    if title_start is not None and annotation_line is not None and title_start < annotation_line:
        title_line = title_start

    if udc_line is not None and annotation_line is not None and udc_line < annotation_line:
        header_range = (udc_line, annotation_line - 1)
    elif first_non_empty is not None and annotation_line is not None and first_non_empty < annotation_line:
        header_range = (first_non_empty, annotation_line - 1)
    else:
        header_range = None

    return ArticleBlocks(
        udc_line=udc_line,
        title_line=title_line,
        annotation_line=annotation_line,
        keywords_line=keywords_line,
        references_line=references_line,
        header_range=header_range,
    )


def write_block_report(doc_path: Path, logs_dir: Path | None, blocks: ArticleBlocks) -> None:
    if logs_dir is None:
        return
    logs_dir.mkdir(parents=True, exist_ok=True)
    payload = {"document": str(doc_path), "blocks": asdict(blocks)}
    out = logs_dir / f"{doc_path.stem}.blocks.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
