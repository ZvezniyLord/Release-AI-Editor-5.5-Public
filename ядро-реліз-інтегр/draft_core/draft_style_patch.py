from __future__ import annotations

import json
import re
import tempfile
import time
import zipfile
from pathlib import Path


def _patch_tabletext_style(docx_path: Path) -> None:
    log_path = docx_path.with_suffix(".tabletext_patch.log")
    try:
        with zipfile.ZipFile(docx_path, "r") as zf:
            styles_xml = zf.read("word/styles.xml").decode("utf-8", errors="ignore")
    except Exception:
        try:
            log_path.write_text("read styles.xml failed", encoding="utf-8")
        except Exception:
            pass
        return

    name_idx = styles_xml.find('w:val="TABLETEXT"')
    if name_idx == -1:
        try:
            log_path.write_text("TABLETEXT style not found", encoding="utf-8")
        except Exception:
            pass
        return

    start_idx = styles_xml.rfind("<w:style", 0, name_idx)
    end_idx = styles_xml.find("</w:style>", name_idx)
    if start_idx == -1 or end_idx == -1:
        try:
            log_path.write_text("TABLETEXT style bounds not found", encoding="utf-8")
        except Exception:
            pass
        return
    end_idx += len("</w:style>")
    style_block = styles_xml[start_idx:end_idx]
    ppr_block = (
        "<w:pPr>"
        '<w:ind w:left="0" w:right="0" w:firstLine="0"/>'
        '<w:spacing w:line="276" w:lineRule="auto" w:before="0" w:after="0"/>'
        "</w:pPr>"
    )
    rpr_block = (
        "<w:rPr>"
        '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
        'w:cs="Times New Roman" w:eastAsia="Times New Roman"/>'
        '<w:sz w:val="24"/><w:szCs w:val="24"/>'
        "</w:rPr>"
    )

    if "<w:pPr>" in style_block:
        style_block = re.sub(r"<w:pPr>.*?</w:pPr>", ppr_block, style_block, flags=re.DOTALL)
    else:
        style_block = style_block.replace("</w:name>", "</w:name>" + ppr_block)

    if "<w:rPr>" in style_block:
        style_block = re.sub(r"<w:rPr>.*?</w:rPr>", rpr_block, style_block, flags=re.DOTALL)
    else:
        style_block = style_block.replace("</w:pPr>", "</w:pPr>" + rpr_block)

    updated_xml = styles_xml[:start_idx] + style_block + styles_xml[end_idx:]

    tmp_path = Path(tempfile.gettempdir()) / f"draft_patch_{docx_path.name}"
    for attempt in range(3):
        try:
            with zipfile.ZipFile(docx_path, "r") as src, zipfile.ZipFile(tmp_path, "w") as dst:
                for item in src.infolist():
                    if item.filename == "word/styles.xml":
                        continue
                    dst.writestr(item, src.read(item.filename))
                dst.writestr("word/styles.xml", updated_xml)
            tmp_path.replace(docx_path)
            try:
                log_path.write_text(f"patched ok (attempt {attempt + 1})", encoding="utf-8")
            except Exception:
                pass
            return
        except Exception:
            time.sleep(0.2)
    return


def _debug_tables_in_range(
    document,
    start_pos: int,
    end_pos: int,
    log_path: Path,
    *,
    source_name: str,
) -> None:
    try:
        rng = document.Range(start_pos, end_pos)
        tables = rng.Tables
    except Exception:
        return
    items = []
    for table_index, table in enumerate(tables, start=1):
        info = {
            "source": source_name,
            "table_index": table_index,
            "style": "",
            "left_indent": None,
        }
        try:
            info["style"] = str(table.Style)
        except Exception:
            pass
        try:
            info["left_indent"] = float(table.LeftIndent)
        except Exception:
            pass
        try:
            cell = table.Cell(1, 1)
            fmt = cell.Range.ParagraphFormat
            info["cell_left_indent"] = float(fmt.LeftIndent)
            info["cell_first_line_indent"] = float(fmt.FirstLineIndent)
        except Exception:
            pass
        items.append(info)
    if items:
        try:
            existing = []
            if log_path.exists():
                try:
                    existing = json.loads(log_path.read_text(encoding="utf-8"))
                except Exception:
                    existing = []
            if isinstance(existing, list):
                existing.extend(items)
                payload = existing
            else:
                payload = items
            log_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
