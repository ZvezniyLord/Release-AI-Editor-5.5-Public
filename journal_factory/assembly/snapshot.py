from __future__ import annotations

import hashlib
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from .ooxml import NS, W, visible_text

DOI_RE = re.compile(r"(?:https?://doi\.org/)?(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", re.I)
ORCID_RE = re.compile(r"\b\d{4}-\d{4}-\d{4}-\d{3}[0-9X]\b")
UDC_RE = re.compile(r"\b(?:UDC|\u0423\u0414\u041a)\s*[: ]\s*([^\n\r]+)", re.I)


@dataclass(frozen=True)
class ParagraphSnapshot:
    index: int
    text: str
    style_id: str | None
    text_hash: str
    in_table: bool


@dataclass(frozen=True)
class DocxSnapshot:
    paragraphs: list[ParagraphSnapshot]
    media_hashes: dict[str, str]
    doi: list[str]
    udc: list[str]
    orcid: list[str]
    table_count: int
    drawing_count: int


def _parent_map(root: ET.Element) -> dict[ET.Element, ET.Element]:
    return {child: parent for parent in root.iter() for child in list(parent)}


def _has_ancestor(node: ET.Element, parents: dict[ET.Element, ET.Element], tag: str) -> bool:
    parent = parents.get(node)
    while parent is not None:
        if parent.tag == tag:
            return True
        parent = parents.get(parent)
    return False


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def snapshot_docx(path: Path) -> DocxSnapshot:
    with zipfile.ZipFile(path) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    root = ET.fromstring(parts["word/document.xml"])
    parents = _parent_map(root)
    paragraphs = []
    for idx, para in enumerate(root.findall(".//w:p", NS)):
        style = para.find("w:pPr/w:pStyle", NS)
        text = visible_text(para)
        paragraphs.append(
            ParagraphSnapshot(
                index=idx,
                text=text,
                style_id=style.get(W + "val") if style is not None else None,
                text_hash=text_hash(text),
                in_table=_has_ancestor(para, parents, W + "tbl"),
            )
        )
    all_text = "\n".join(item.text for item in paragraphs if item.text)
    media_hashes = {
        name: hashlib.sha256(payload).hexdigest()
        for name, payload in parts.items()
        if name.startswith("word/media/")
    }
    document_xml = parts["word/document.xml"].decode("utf-8", errors="ignore")
    return DocxSnapshot(
        paragraphs=paragraphs,
        media_hashes=media_hashes,
        doi=sorted(set(DOI_RE.findall(all_text))),
        udc=sorted(set(UDC_RE.findall(all_text))),
        orcid=sorted(set(ORCID_RE.findall(all_text))),
        table_count=len(root.findall(".//w:tbl", NS)),
        drawing_count=document_xml.count("<w:drawing"),
    )
