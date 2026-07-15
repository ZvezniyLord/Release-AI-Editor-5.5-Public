# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import json
import zipfile
import xml.etree.ElementTree as ET

TOC_VISUAL_CONTRACT_INVALID = "TOC_VISUAL_CONTRACT_INVALID"
EXPECTED_COLUMN_WIDTHS_TWIPS = [661, 8170, 797]

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def _normalize_spaces(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _text_from_node(node: ET.Element) -> str:
    chunks = [text.text or "" for text in node.findall(".//w:t", NS)]
    return _normalize_spaces("".join(chunks))


def _paragraph_text(paragraph: ET.Element) -> str:
    return _normalize_spaces("".join(node.text or "" for node in paragraph.findall(".//w:t", NS)))


def _paragraph_style(paragraph: ET.Element) -> str:
    style = paragraph.find("w:pPr/w:pStyle", NS)
    if style is None:
        return ""
    return style.get(f"{{{NS['w']}}}val") or ""


def _canonical_style(style: str) -> str:
    return "".join(ch for ch in style.casefold() if ch.isalnum())


def _grid_widths(table: ET.Element) -> list[int]:
    widths: list[int] = []
    for col in table.findall("w:tblGrid/w:gridCol", NS):
        value = col.get(f"{{{NS['w']}}}w")
        try:
            widths.append(int(value or "0"))
        except ValueError:
            widths.append(0)
    return widths


def _row_texts(row: ET.Element) -> list[str]:
    return [_text_from_node(cell) for cell in row.findall("w:tc", NS)]


def _central_nonempty_paragraphs(row: ET.Element) -> list[ET.Element]:
    cells = row.findall("w:tc", NS)
    if len(cells) != 3:
        return []
    return [p for p in cells[1].findall("w:p", NS) if _paragraph_text(p)]


def audit_toc_docx(
    docx_path: Path,
    *,
    expected_journal_sections: int = 2,
    expected_articles: int = 3,
    expected_free_listener_rows: int = 1,
) -> dict:
    docx_path = Path(docx_path)
    errors: list[dict[str, str]] = []
    rows_report: list[dict[str, object]] = []

    try:
        with zipfile.ZipFile(docx_path, "r") as zf:
            document_xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
    except Exception as error:
        return {
            "status": "FAIL",
            "errors": [{"code": TOC_VISUAL_CONTRACT_INVALID, "message": f"cannot read DOCX: {error}"}],
        }

    root = ET.fromstring(document_xml)
    body = root.find("w:body", NS)
    tables = body.findall("w:tbl", NS) if body is not None else []

    if len(tables) != 1:
        errors.append({
            "code": TOC_VISUAL_CONTRACT_INVALID,
            "message": f"expected one physical TOC table, found {len(tables)}",
        })

    journal_section_rows = 0
    article_rows = 0
    free_listener_rows = 0
    widths: list[int] = []

    if tables:
        table = tables[0]
        widths = _grid_widths(table)
        if widths != EXPECTED_COLUMN_WIDTHS_TWIPS:
            errors.append({
                "code": TOC_VISUAL_CONTRACT_INVALID,
                "message": f"expected grid widths {EXPECTED_COLUMN_WIDTHS_TWIPS}, found {widths}",
            })

        for row_index, row in enumerate(table.findall("w:tr", NS), start=1):
            cells = row.findall("w:tc", NS)
            if len(cells) != 3:
                errors.append({
                    "code": TOC_VISUAL_CONTRACT_INVALID,
                    "message": f"row {row_index}: expected 3 cells, found {len(cells)}",
                })
                continue

            texts = _row_texts(row)
            if texts[0] or texts[2]:
                errors.append({
                    "code": TOC_VISUAL_CONTRACT_INVALID,
                    "message": f"row {row_index}: side cells must be empty",
                })

            if any("анкета" in text.casefold() for text in texts):
                errors.append({
                    "code": TOC_VISUAL_CONTRACT_INVALID,
                    "message": f"row {row_index}: form/noise fragment leaked into TOC",
                })

            paragraphs = _central_nonempty_paragraphs(row)
            styles = [_canonical_style(_paragraph_style(p)) for p in paragraphs]
            kind = "unknown"
            if styles == ["tabsec"]:
                kind = "section"
                journal_section_rows += 1
            elif styles == ["tabpip", "tabtaitl"]:
                kind = "article"
                article_rows += 1
            elif styles == ["tabpip"]:
                kind = "free_listener"
                free_listener_rows += 1
            else:
                errors.append({
                    "code": TOC_VISUAL_CONTRACT_INVALID,
                    "message": f"row {row_index}: unexpected central paragraph styles {styles}",
                })
            rows_report.append({
                "row": row_index,
                "kind": kind,
                "central_paragraph_count": len(paragraphs),
                "central_styles": styles,
                "side_cells_empty": not texts[0] and not texts[2],
            })

    expected_section_style_rows = expected_journal_sections + (1 if expected_free_listener_rows else 0)
    if journal_section_rows != expected_section_style_rows:
        errors.append({
            "code": TOC_VISUAL_CONTRACT_INVALID,
            "message": (
                f"expected {expected_section_style_rows} Tab_SEC rows "
                f"({expected_journal_sections} sections + free-listener header), found {journal_section_rows}"
            ),
        })
    if article_rows != expected_articles:
        errors.append({
            "code": TOC_VISUAL_CONTRACT_INVALID,
            "message": f"expected {expected_articles} article rows, found {article_rows}",
        })
    if free_listener_rows != expected_free_listener_rows:
        errors.append({
            "code": TOC_VISUAL_CONTRACT_INVALID,
            "message": f"expected {expected_free_listener_rows} free-listener rows, found {free_listener_rows}",
        })

    return {
        "status": "PASS" if not errors else "FAIL",
        "docx": str(docx_path),
        "contract": {
            "table_count": len(tables),
            "column_widths_twips": widths,
            "expected_column_widths_twips": EXPECTED_COLUMN_WIDTHS_TWIPS,
            "text_column": 2,
            "journal_sections": expected_journal_sections,
            "articles": expected_articles,
            "free_listener_rows": expected_free_listener_rows,
        },
        "rows": rows_report,
        "errors": errors,
    }


def write_audit_json(report: dict, output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
