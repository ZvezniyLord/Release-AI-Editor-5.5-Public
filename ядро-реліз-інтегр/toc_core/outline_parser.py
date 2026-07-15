# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import zipfile
import xml.etree.ElementTree as ET

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}

DEFAULT_NAME_LEVELS = {
    "heading 1": 1,
    "heading 2": 2,
    "heading 3": 3,
    "title": 1,
    "title 1": 1,
    "назва 1": 1,
    "назва1": 1,
    "заголовок 1": 1,
    "заголовок 2": 2,
    "заголовок 3": 3,
    "section": 1,
    "секція": 1,
    "секція заголовок": 1,
}

DEFAULT_ID_LEVELS = {
    "heading1": 1,
    "heading 1": 1,
    "heading2": 2,
    "heading 2": 2,
    "heading3": 3,
    "heading 3": 3,
    "title": 1,
    "title1": 1,
    "title 1": 1,
    "section": 1,
    "секція": 1,
    "секція заголовок": 1,
}


@dataclass(frozen=True)
class OutlineItem:
    level: int
    text: str


@dataclass(frozen=True)
class SectionItem:
    authors: str
    title: str


@dataclass(frozen=True)
class Section:
    name: str
    items: list[SectionItem]


def _normalize_spaces(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _text_from_paragraph(p: ET.Element) -> str:
    chunks: list[str] = []
    for node in p.findall(".//w:t", NS):
        if node.text:
            chunks.append(node.text)
    return _normalize_spaces("".join(chunks))


def _load_styles_map(styles_xml: str) -> dict[str, dict[str, str | int | None]]:
    root = ET.fromstring(styles_xml)
    styles: dict[str, dict[str, str | int | None]] = {}
    for style in root.findall(".//w:style", NS):
        if style.get(f"{{{NS['w']}}}type") != "paragraph":
            continue
        style_id = style.get(f"{{{NS['w']}}}styleId")
        if not style_id:
            continue
        name_node = style.find("w:name", NS)
        name = name_node.get(f"{{{NS['w']}}}val") if name_node is not None else None
        based_on = None
        based_on_node = style.find("w:basedOn", NS)
        if based_on_node is not None:
            based_on = based_on_node.get(f"{{{NS['w']}}}val")
        outline = None
        outline_node = style.find("w:pPr/w:outlineLvl", NS)
        if outline_node is not None:
            val = outline_node.get(f"{{{NS['w']}}}val")
            try:
                outline = int(val)
            except Exception:
                outline = None
        styles[style_id] = {"name": name, "based_on": based_on, "outline": outline}
    return styles


def _resolve_outline(style_id: str, styles: dict[str, dict[str, str | int | None]], depth: int = 0) -> int | None:
    if depth > 10:
        return None
    info = styles.get(style_id)
    if not info:
        return None
    outline = info.get("outline")
    if isinstance(outline, int):
        return outline
    based_on = info.get("based_on")
    if isinstance(based_on, str) and based_on:
        return _resolve_outline(based_on, styles, depth + 1)
    return None


def _level_from_style_name(style_name: str | None) -> int | None:
    if not style_name:
        return None
    key = style_name.casefold().strip()
    direct = DEFAULT_NAME_LEVELS.get(key)
    if direct is not None:
        return direct
    if "section" in key or "секц" in key:
        return 1
    return None


def _level_from_style_id(style_id: str | None) -> int | None:
    if not style_id:
        return None
    key = style_id.casefold().strip()
    return DEFAULT_ID_LEVELS.get(key)


def _level_from_outline_val(val: int | None) -> int | None:
    if val is None:
        return None
    if val < 0:
        return None
    if val <= 8:
        return val + 1
    return None


def _iter_body_paragraphs(body: ET.Element) -> Iterable[ET.Element]:
    for child in list(body):
        tag = child.tag
        if tag == f"{{{NS['w']}}}p":
            yield child
        elif tag == f"{{{NS['w']}}}tbl":
            continue


def parse_outline(docx_path: Path) -> list[OutlineItem]:
    docx_path = Path(docx_path)
    with zipfile.ZipFile(docx_path, "r") as zf:
        document_xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
        styles_xml = None
        try:
            styles_xml = zf.read("word/styles.xml").decode("utf-8", errors="ignore")
        except Exception:
            styles_xml = ""

    styles = _load_styles_map(styles_xml) if styles_xml else {}
    doc_root = ET.fromstring(document_xml)
    body = doc_root.find("w:body", NS)
    if body is None:
        return []

    items: list[OutlineItem] = []
    for p in _iter_body_paragraphs(body):
        text = _text_from_paragraph(p)
        if not text:
            continue
        ppr = p.find("w:pPr", NS)
        style_id = None
        outline_val = None
        if ppr is not None:
            pstyle = ppr.find("w:pStyle", NS)
            if pstyle is not None:
                style_id = pstyle.get(f"{{{NS['w']}}}val")
            outline_node = ppr.find("w:outlineLvl", NS)
            if outline_node is not None:
                try:
                    outline_val = int(outline_node.get(f"{{{NS['w']}}}val"))
                except Exception:
                    outline_val = None

        style_name = None
        if style_id and style_id in styles:
            style_name = styles[style_id].get("name")  # type: ignore[assignment]

        # Prefer explicit outline level if present (it can override style name).
        level = _level_from_outline_val(outline_val)
        if level is None and style_id:
            resolved_outline = _resolve_outline(style_id, styles)
            level = _level_from_outline_val(resolved_outline)
        if level is None:
            level = _level_from_style_name(style_name)
        if level is None:
            level = _level_from_style_id(style_id)
        if level in {1, 2, 3}:
            items.append(OutlineItem(level=level, text=text))

    return items


def build_sections(items: Iterable[OutlineItem]) -> list[Section]:
    sections: list[Section] = []
    current_section: Section | None = None
    current_authors: list[str] = []
    last_level = None
    for item in items:
        if item.level == 1:
            current_section = Section(name=item.text, items=[])
            sections.append(current_section)
            current_authors = []
            last_level = 1
            continue
        if item.level == 2:
            if last_level != 2:
                current_authors = []
            if item.text:
                current_authors.append(item.text)
            last_level = 2
            continue
        if item.level == 3:
            if current_section is None:
                current_section = Section(name="Без секції", items=[])
                sections.append(current_section)
            authors_text = ", ".join([a for a in current_authors if a])
            current_section.items.append(SectionItem(authors=authors_text, title=item.text))
            last_level = 3
    return sections
