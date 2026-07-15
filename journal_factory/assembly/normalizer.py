from __future__ import annotations

from collections import deque
from xml.etree import ElementTree as ET

from .ooxml import NS, W, local_name


def paragraph_style_id(paragraph: ET.Element) -> str | None:
    style = paragraph.find("w:pPr/w:pStyle", NS)
    return style.get(W + "val") if style is not None else None


def set_paragraph_style(paragraph: ET.Element, style_id: str) -> None:
    ppr = paragraph.find("w:pPr", NS)
    if ppr is None:
        ppr = ET.Element(W + "pPr")
        paragraph.insert(0, ppr)
    style = ppr.find("w:pStyle", NS)
    if style is None:
        style = ET.Element(W + "pStyle")
        ppr.insert(0, style)
    style.set(W + "val", style_id)


def known_style_ids(styles_root: ET.Element) -> set[str]:
    return {
        style.get(W + "styleId")
        for style in styles_root.findall(".//w:style", NS)
        if style.get(W + "styleId")
    }


def remove_dangling_style_references(document_root: ET.Element, styles_root: ET.Element) -> dict[str, int]:
    """Remove character/table style references not present in final styles.xml."""
    known = known_style_ids(styles_root)
    removed_rstyle = 0
    removed_tblstyle = 0
    for parent in document_root.iter():
        for child in list(parent):
            name = local_name(child.tag)
            if name == "rStyle" and child.get(W + "val") not in known:
                parent.remove(child)
                removed_rstyle += 1
            elif name == "tblStyle" and child.get(W + "val") not in known:
                parent.remove(child)
                removed_tblstyle += 1
    return {"removed_unknown_rStyle": removed_rstyle, "removed_unknown_tblStyle": removed_tblstyle}


def dedupe_drawing_ids(document_root: ET.Element) -> int:
    next_id = 1
    reassigned = 0
    for node in document_root.iter():
        if local_name(node.tag) in {"docPr", "cNvPr"} and "id" in node.attrib:
            node.set("id", str(next_id))
            next_id += 1
            reassigned += 1
    return reassigned


def dedupe_bookmark_ids(document_root: ET.Element) -> int:
    seen: set[str] = set()
    next_id = 1
    for node in document_root.iter():
        if local_name(node.tag) in {"bookmarkStart", "bookmarkEnd"}:
            value = node.get(W + "id")
            if value and value.isdigit():
                next_id = max(next_id, int(value) + 1)

    pending: dict[str, deque[str]] = {}
    changed = 0
    for node in document_root.iter():
        name = local_name(node.tag)
        if name == "bookmarkStart":
            old = node.get(W + "id")
            if old is None:
                continue
            if old in seen:
                new = str(next_id)
                next_id += 1
                node.set(W + "id", new)
                pending.setdefault(old, deque()).append(new)
                changed += 1
            else:
                seen.add(old)
        elif name == "bookmarkEnd":
            old = node.get(W + "id")
            if old in pending and pending[old]:
                node.set(W + "id", pending[old].popleft())
                changed += 1
    return changed


def normalize_internal_ids(document_root: ET.Element) -> dict[str, int]:
    return {
        "reassigned_drawing_ids": dedupe_drawing_ids(document_root),
        "reassigned_bookmark_ids": dedupe_bookmark_ids(document_root),
    }
