from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph


TABLE_MARKER_RE = re.compile(r"^\s*(таблиця|таблица|table)\s*\d+\b", re.IGNORECASE)
FIGURE_MARKER_RE = re.compile(r"^\s*(рис\.?|рисунок|figure|fig\.?)\s*\d+\b", re.IGNORECASE)
CAPTION_CONTINUATION_RE = re.compile(r"^\s*[•·▪●◦]", re.IGNORECASE)
CAPTION_STYLE_CANDIDATES = ("РисПід", "РисПод", "Caption")


def _paragraph_text_from_elem(p_elem) -> str:
    chunks: list[str] = []
    for node in p_elem.findall(".//" + qn("w:t")):
        chunks.append(node.text or "")
    return "".join(chunks).strip()


def _paragraph_has_graphics_from_elem(p_elem) -> bool:
    for node in p_elem.iter():
        tag = str(node.tag)
        if tag.endswith("}drawing") or tag.endswith("}pict") or tag.endswith("}object"):
            return True
    return False


def _is_empty_paragraph_elem(p_elem) -> bool:
    return not _paragraph_text_from_elem(p_elem) and not _paragraph_has_graphics_from_elem(p_elem)


def _is_paragraph_elem(elem) -> bool:
    return elem is not None and str(elem.tag).endswith("}p")


def _is_table_elem(elem) -> bool:
    return elem is not None and str(elem.tag).endswith("}tbl")


def _insert_blank_before(elem) -> None:
    blank = OxmlElement("w:p")
    elem.addprevious(blank)


def _insert_blank_after(elem) -> None:
    blank = OxmlElement("w:p")
    elem.addnext(blank)


def _ensure_single_blank_before_elem(elem) -> bool:
    changed = False
    prev = elem.getprevious()
    if prev is None:
        return changed

    if _is_paragraph_elem(prev):
        if not _is_empty_paragraph_elem(prev):
            _insert_blank_before(elem)
            changed = True
        else:
            walker = prev.getprevious()
            while _is_paragraph_elem(walker) and _is_empty_paragraph_elem(walker):
                older = walker.getprevious()
                walker.getparent().remove(walker)
                changed = True
                walker = older
    else:
        _insert_blank_before(elem)
        changed = True
    return changed


def _ensure_single_blank_before_para(paragraph: Paragraph) -> bool:
    return _ensure_single_blank_before_elem(paragraph._p)


def _find_preceding_graphic_paragraph_elem(paragraph: Paragraph):
    walker = paragraph._p.getprevious()
    while _is_paragraph_elem(walker):
        if _paragraph_has_graphics_from_elem(walker):
            return walker
        if _paragraph_text_from_elem(walker):
            return None
        walker = walker.getprevious()
    return None


def _ensure_single_blank_after_tables(doc: Document) -> bool:
    changed = False
    body = doc._body._element
    tables = [child for child in list(body) if _is_table_elem(child)]
    for tbl in tables:
        nxt = tbl.getnext()
        if nxt is None:
            _insert_blank_after(tbl)
            changed = True
            continue
        if _is_paragraph_elem(nxt):
            if not _is_empty_paragraph_elem(nxt):
                _insert_blank_after(tbl)
                changed = True
            else:
                walker = nxt.getnext()
                while _is_paragraph_elem(walker) and _is_empty_paragraph_elem(walker):
                    newer = walker.getnext()
                    walker.getparent().remove(walker)
                    changed = True
                    walker = newer
        else:
            _insert_blank_after(tbl)
            changed = True
    return changed


def _apply_caption_style(paragraph: Paragraph) -> bool:
    for style_name in CAPTION_STYLE_CANDIDATES:
        try:
            if paragraph.style and paragraph.style.name == style_name:
                return False
            paragraph.style = style_name
            return True
        except Exception:
            continue
    return False


def _set_right_alignment(paragraph: Paragraph) -> bool:
    if paragraph.alignment == WD_ALIGN_PARAGRAPH.RIGHT:
        return False
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    return True


def _apply_caption_rules(doc: Document) -> bool:
    changed = False
    for para in doc.paragraphs:
        text = (para.text or "").strip()
        if not text:
            continue

        is_table_caption = bool(TABLE_MARKER_RE.search(text))
        is_figure_caption = bool(FIGURE_MARKER_RE.search(text))
        if not (is_table_caption or is_figure_caption):
            continue

        if _ensure_single_blank_before_para(para):
            changed = True

        if is_figure_caption:
            graphic_elem = _find_preceding_graphic_paragraph_elem(para)
            if graphic_elem is not None:
                if _ensure_single_blank_before_elem(graphic_elem):
                    changed = True
            if _apply_caption_style(para):
                changed = True
            next_elem = para._p.getnext()
            if next_elem is None or not _is_paragraph_elem(next_elem):
                _insert_blank_after(para._p)
                changed = True
                continue
            if not _is_empty_paragraph_elem(next_elem):
                next_para = Paragraph(next_elem, para._parent)
                next_text = (next_para.text or "").strip()
                if CAPTION_CONTINUATION_RE.search(next_text):
                    continue
                _insert_blank_after(para._p)
                changed = True
                continue
            walker = next_elem.getnext()
            while _is_paragraph_elem(walker) and _is_empty_paragraph_elem(walker):
                walker = walker.getnext()
            if _is_paragraph_elem(walker):
                walker_para = Paragraph(walker, para._parent)
                walker_text = (walker_para.text or "").strip()
                if CAPTION_CONTINUATION_RE.search(walker_text):
                    next_elem.getparent().remove(next_elem)
                    changed = True
                    continue
            walker = next_elem.getnext()
            while _is_paragraph_elem(walker) and _is_empty_paragraph_elem(walker):
                newer = walker.getnext()
                walker.getparent().remove(walker)
                changed = True
                walker = newer
            continue

        if _set_right_alignment(para):
            changed = True

        next_elem = para._p.getnext()
        if not _is_paragraph_elem(next_elem):
            continue
        next_para = Paragraph(next_elem, para._parent)
        next_text = (next_para.text or "").strip()
        if not next_text:
            continue
        if TABLE_MARKER_RE.search(next_text) or FIGURE_MARKER_RE.search(next_text):
            continue
        if _apply_caption_style(next_para):
            changed = True
    return changed


def normalize_caption_layout(doc_path: Path) -> Path:
    doc = Document(doc_path)
    changed = False
    if _ensure_single_blank_after_tables(doc):
        changed = True
    if _apply_caption_rules(doc):
        changed = True
    if changed:
        doc.save(doc_path)
    return doc_path
