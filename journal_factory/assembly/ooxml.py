from __future__ import annotations

import re
from xml.etree import ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"

NS = {"w": W_NS, "r": R_NS, "m": M_NS, "mc": MC_NS}
W = f"{{{W_NS}}}"
R = f"{{{R_NS}}}"
REL = f"{{{REL_NS}}}"
CT = f"{{{CT_NS}}}"
MC = f"{{{MC_NS}}}"

OOXML_NAMESPACES = {
    "w": W_NS,
    "r": R_NS,
    "m": M_NS,
    "mc": MC_NS,
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "wp14": "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "a14": "http://schemas.microsoft.com/office/drawing/2010/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "v": "urn:schemas-microsoft-com:vml",
    "o": "urn:schemas-microsoft-com:office:office",
    "w10": "urn:schemas-microsoft-com:office:word",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
    "w16": "http://schemas.microsoft.com/office/word/2018/wordml",
    "w16cex": "http://schemas.microsoft.com/office/word/2018/wordml/cex",
    "w16cid": "http://schemas.microsoft.com/office/word/2016/wordml/cid",
    "w16sdtdh": "http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash",
    "w16se": "http://schemas.microsoft.com/office/word/2015/wordml/symex",
    "wpg": "http://schemas.microsoft.com/office/word/2010/wordprocessingGroup",
    "wps": "http://schemas.microsoft.com/office/word/2010/wordprocessingShape",
    "wne": "http://schemas.microsoft.com/office/word/2006/wordml",
}


def register_ooxml_namespaces() -> None:
    for prefix, uri in OOXML_NAMESPACES.items():
        ET.register_namespace(prefix, uri)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def serialize_xml(root: ET.Element, default_namespace: str | None = None) -> bytes:
    register_ooxml_namespaces()
    if default_namespace:
        ET.register_namespace("", default_namespace)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def clean_mc_ignorable(xml_bytes: bytes) -> bytes:
    """Remove mc:Ignorable prefixes that are not declared after serialization."""
    text = xml_bytes.decode("utf-8")
    root_match = re.search(r"<w:document\b[^>]*>", text)
    if not root_match:
        return xml_bytes
    root_tag = root_match.group(0)
    declared = set(re.findall(r"xmlns:([A-Za-z0-9_]+)=", root_tag))

    def replace(match: re.Match[str]) -> str:
        prefixes = [item for item in match.group(1).split() if item in declared]
        return f'mc:Ignorable="{" ".join(prefixes)}"'

    cleaned = re.sub(r'mc:Ignorable="([^"]*)"', replace, root_tag)
    return (text[: root_match.start()] + cleaned + text[root_match.end() :]).encode("utf-8")


def visible_text(element: ET.Element) -> str:
    chunks: list[str] = []

    def walk(node: ET.Element) -> None:
        if node.tag == W + "t":
            chunks.append(node.text or "")
        elif node.tag == W + "tab":
            chunks.append("\t")
        elif node.tag in {W + "br", W + "cr"}:
            chunks.append("\n")
        for child in list(node):
            walk(child)
        if node.tag in {W + "p", W + "tc"}:
            chunks.append("\n")

    walk(element)
    return " ".join("".join(chunks).replace("\u00a0", " ").split())


register_ooxml_namespaces()
