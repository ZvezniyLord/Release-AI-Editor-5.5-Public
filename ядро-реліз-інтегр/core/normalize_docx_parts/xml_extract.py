from __future__ import annotations

from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

from docx.oxml import OxmlElement
from docx.oxml.ns import qn


ARABIC_SCRIPT_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")


def load_numbering(zf: zipfile.ZipFile, ns: dict[str, str]) -> dict[tuple[str, int], str]:
    # key: (numId, ilvl) -> numFmt
    try:
        numbering_xml = zf.read("word/numbering.xml").decode("utf-8", errors="ignore")
    except Exception:
        return {}
    root = ET.fromstring(numbering_xml)
    abstract_map: dict[str, dict[int, str]] = {}
    for absnum in root.findall("w:abstractNum", ns):
        abs_id = absnum.get(f"{{{ns['w']}}}abstractNumId")
        if not abs_id:
            continue
        level_map: dict[int, str] = {}
        for lvl in absnum.findall("w:lvl", ns):
            ilvl = lvl.get(f"{{{ns['w']}}}ilvl")
            numfmt = lvl.find("w:numFmt", ns)
            if ilvl is None or numfmt is None:
                continue
            fmt = numfmt.get(f"{{{ns['w']}}}val") or ""
            try:
                level_map[int(ilvl)] = fmt
            except Exception:
                continue
        abstract_map[abs_id] = level_map

    mapping: dict[tuple[str, int], str] = {}
    for num in root.findall("w:num", ns):
        num_id = num.get(f"{{{ns['w']}}}numId")
        abs_id_node = num.find("w:abstractNumId", ns)
        if not num_id or abs_id_node is None:
            continue
        abs_id = abs_id_node.get(f"{{{ns['w']}}}val")
        if not abs_id:
            continue
        level_map = abstract_map.get(abs_id, {})
        for ilvl, fmt in level_map.items():
            mapping[(num_id, ilvl)] = fmt
    return mapping


def load_rels(zf: zipfile.ZipFile) -> dict[str, str]:
    try:
        rels_xml = zf.read("word/_rels/document.xml.rels").decode("utf-8", errors="ignore")
    except Exception:
        return {}
    root = ET.fromstring(rels_xml)
    rels: dict[str, str] = {}
    for rel in root.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
        rid = rel.get("Id")
        target = rel.get("Target")
        if rid and target:
            rels[rid] = target
    return rels


def image_sources(zf: zipfile.ZipFile, rels: dict[str, str], rids: list[str]) -> list[tuple[bytes, str]]:
    out: list[tuple[bytes, str]] = []
    for rid in rids:
        target = rels.get(rid)
        if not target:
            continue
        target = f"word/{target}"
        ext = Path(target).suffix.lower()
        try:
            blob = zf.read(target)
        except Exception:
            continue
        out.append((blob, ext))
    return out


def is_supported_image_ext(ext: str) -> bool:
    return ext in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff"}


def paragraph_text(p: ET.Element, ns: dict[str, str]) -> str:
    chunks: list[str] = []
    for node in p.iter():
        tag = node.tag
        if tag == f"{{{ns['w']}}}t":
            if node.text:
                chunks.append(node.text)
        elif tag == f"{{{ns['w']}}}br":
            br_type = node.get(qn("w:type"))
            if br_type != "page":
                chunks.append("\n")
    return "".join(chunks).strip()


def run_bold_italic(rpr: ET.Element | None, ns: dict[str, str]) -> tuple[bool, bool]:
    if rpr is None:
        return False, False
    bold = False
    italic = False
    b = rpr.find("w:b", ns)
    if b is not None:
        val = b.get(f"{{{ns['w']}}}val")
        bold = False if val == "0" else True
    i = rpr.find("w:i", ns)
    if i is not None:
        val = i.get(f"{{{ns['w']}}}val")
        italic = False if val == "0" else True
    return bold, italic


def run_vertical_align(rpr: ET.Element | None, ns: dict[str, str]) -> tuple[bool, bool]:
    if rpr is None:
        return False, False
    vert_align = rpr.find("w:vertAlign", ns)
    if vert_align is None:
        return False, False
    value = (vert_align.get(f"{{{ns['w']}}}val") or "").strip().lower()
    return value == "superscript", value == "subscript"


def run_segments(
    r: ET.Element,
    ns: dict[str, str],
    math_state: dict[str, int] | None = None,
) -> list[tuple[str, bool, bool, bool, bool]]:
    segments: list[tuple[str, bool, bool, bool, bool]] = []
    rpr = r.find("w:rPr", ns)
    bold, italic = run_bold_italic(rpr, ns)
    superscript, subscript = run_vertical_align(rpr, ns)
    for node in r:
        if node.tag == f"{{{ns['w']}}}t":
            if node.text:
                segments.append((node.text, bold, italic, superscript, subscript))
        elif node.tag == f"{{{ns['w']}}}br":
            br_type = node.get(qn("w:type"))
            if br_type != "page":
                segments.append(("\n", bold, italic, superscript, subscript))
        elif node.tag in {f"{{{ns['m']}}}oMath", f"{{{ns['m']}}}oMathPara"}:
            token = _next_math_token(math_state)
            if token:
                segments.append((token, bold, italic, superscript, subscript))
    return segments


def _next_math_token(math_state: dict[str, int] | None) -> str:
    if math_state is None:
        return ""
    math_state["count"] = math_state.get("count", 0) + 1
    return f"<<OMATH_PLACEHOLDER_{math_state['count']}>>"


def paragraph_runs(
    p: ET.Element,
    ns: dict[str, str],
    math_state: dict[str, int] | None = None,
) -> list[tuple[str, bool, bool, bool, bool]]:
    runs: list[tuple[str, bool, bool, bool, bool]] = []
    for child in list(p):
        tag = child.tag
        if tag == f"{{{ns['w']}}}r":
            runs.extend(run_segments(child, ns, math_state))
        elif tag in {f"{{{ns['m']}}}oMath", f"{{{ns['m']}}}oMathPara"}:
            token = _next_math_token(math_state)
            if token:
                runs.append((token, False, False, False, False))
        elif tag == f"{{{ns['w']}}}hyperlink":
            for r in child.findall("w:r", ns):
                runs.extend(run_segments(r, ns, math_state))
        elif tag == f"{{{ns['w']}}}fldSimple":
            for r in child.findall("w:r", ns):
                runs.extend(run_segments(r, ns, math_state))
        elif tag == f"{{{ns['w']}}}smartTag":
            for r in child.findall(".//w:r", ns):
                runs.extend(run_segments(r, ns, math_state))
    return runs


def paragraph_chart_count(p: ET.Element, ns: dict[str, str]) -> int:
    try:
        return len(p.findall(".//c:chart", ns))
    except Exception:
        return 0


def split_runs_on_breaks(
    runs: list[tuple[str, bool, bool, bool, bool]]
) -> list[list[tuple[str, bool, bool, bool, bool]]]:
    lines: list[list[tuple[str, bool, bool, bool, bool]]] = [[]]
    for text, bold, italic, superscript, subscript in runs:
        parts = text.split("\n")
        for idx, part in enumerate(parts):
            if part:
                lines[-1].append((part, bold, italic, superscript, subscript))
            if idx < len(parts) - 1:
                lines.append([])
    return [line for line in lines if any(seg[0] for seg in line)]


def add_runs(paragraph, runs: list[tuple[str, bool, bool, bool, bool]]) -> None:
    for text, bold, italic, superscript, subscript in runs:
        if not text:
            continue
        run = paragraph.add_run(text)
        if bold:
            run.bold = True
        if italic:
            run.italic = True
        if superscript:
            run.font.superscript = True
        if subscript:
            run.font.subscript = True
        if ARABIC_SCRIPT_RE.search(text):
            rpr = run._r.get_or_add_rPr()
            rtl = rpr.find(qn("w:rtl"))
            if rtl is None:
                rpr.append(OxmlElement("w:rtl"))
            rfonts = rpr.find(qn("w:rFonts"))
            if rfonts is None:
                rfonts = OxmlElement("w:rFonts")
                rpr.append(rfonts)
            rfonts.set(qn("w:hint"), "cs")
            lang = rpr.find(qn("w:lang"))
            if lang is None:
                lang = OxmlElement("w:lang")
                rpr.append(lang)
            lang.set(qn("w:bidi"), "fa-IR")


def paragraph_image_rids(p: ET.Element, ns: dict[str, str]) -> list[str]:
    rids: list[str] = []
    for blip in p.findall(".//a:blip", ns):
        rid = blip.get(f"{{{ns['r']}}}embed")
        if rid:
            rids.append(rid)
    for imdata in p.findall(".//v:imagedata", ns):
        rid = imdata.get(f"{{{ns['r']}}}id")
        if rid:
            rids.append(rid)
    return rids


def paragraph_textboxes(p: ET.Element, ns: dict[str, str]) -> list[str]:
    boxes: list[str] = []
    for tx in p.findall(".//w:txbxContent", ns):
        parts: list[str] = []
        for tp in tx.findall(".//w:p", ns):
            t = paragraph_text(tp, ns)
            if t:
                parts.append(t)
        if parts:
            boxes.append("\n".join(parts))
    return boxes


def paragraph_unsupported_drawing_count(p: ET.Element, ns: dict[str, str]) -> int:
    # SmartArt/diagram objects are encoded via dgm:relIds and are not normal blip images/charts.
    try:
        return len(p.findall(".//dgm:relIds", ns))
    except Exception:
        return 0
