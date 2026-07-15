from __future__ import annotations

import json
import zipfile
from pathlib import Path


def _style_names_from_docx(path: Path) -> set[str]:
    with zipfile.ZipFile(path, "r") as zf:
        try:
            styles_xml = zf.read("word/styles.xml").decode("utf-8", errors="ignore")
        except Exception:
            return set()
    import xml.etree.ElementTree as ET

    NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    names: set[str] = set()
    try:
        root = ET.fromstring(styles_xml)
    except Exception:
        return names
    for style in root.findall(".//w:style", NS):
        name_node = style.find("w:name", NS)
        if name_node is not None:
            val = name_node.get(f"{{{NS['w']}}}val")
            if val:
                names.add(val)
    return names


def _media_count(path: Path) -> int:
    with zipfile.ZipFile(path, "r") as zf:
        return sum(1 for name in zf.namelist() if name.startswith("word/media/"))


def _table_count(path: Path) -> int:
    with zipfile.ZipFile(path, "r") as zf:
        xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
    return xml.count("<w:tbl")


def _text_len(path: Path) -> int:
    with zipfile.ZipFile(path, "r") as zf:
        xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
    # rough text length
    return xml.count("<w:t")


def eval_docx(before: Path, after: Path, template: Path | None = None) -> dict[str, object]:
    before_styles = _style_names_from_docx(before)
    after_styles = _style_names_from_docx(after)
    template_styles = _style_names_from_docx(template) if template else set()

    return {
        "before": {
            "tables": _table_count(before),
            "images": _media_count(before),
            "text_nodes": _text_len(before),
            "styles": len(before_styles),
        },
        "after": {
            "tables": _table_count(after),
            "images": _media_count(after),
            "text_nodes": _text_len(after),
            "styles": len(after_styles),
        },
        "style_diff": {
            "extra_after": sorted(after_styles - before_styles),
            "missing_after": sorted(before_styles - after_styles),
        },
        "template_diff": {
            "extra_after": sorted(after_styles - template_styles) if template_styles else [],
            "missing_after": sorted(template_styles - after_styles) if template_styles else [],
        },
    }


def write_report(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
