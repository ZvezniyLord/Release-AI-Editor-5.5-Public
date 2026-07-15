from __future__ import annotations

import argparse
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "v": "urn:schemas-microsoft-com:vml",
    "dgm": "http://schemas.openxmlformats.org/drawingml/2006/diagram",
}

MODULE_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = MODULE_ROOT / "assets" / "templates" / "Jurnal.dotx"

try:
    from core.normalize_docx_parts.rebuild_pipeline import rebuild_document_from_body
    from core.normalize_docx_parts.table_builder import (
        clear_document_body as _clear_document_body,
        ensure_refer_style as _ensure_refer_style,
        ensure_table_text_style as _ensure_table_text_style,
        load_template_document as _load_template_document,
    )
    from core.normalize_docx_parts.unsupported_drawing import (
        replace_unsupported_drawings_or_fallback as _replace_unsupported_drawings_or_fallback,
    )
    from core.normalize_docx_parts.word_replace import (
        replace_chart_placeholders as _replace_chart_placeholders,
        replace_image_placeholders as _replace_image_placeholders,
        replace_math_placeholders as _replace_math_placeholders,
    )
    from core.normalize_docx_parts.xml_extract import (
        load_numbering as _load_numbering,
        load_rels as _load_rels,
    )
except Exception:
    from normalize_docx_parts.rebuild_pipeline import rebuild_document_from_body  # type: ignore
    from normalize_docx_parts.table_builder import (  # type: ignore
        clear_document_body as _clear_document_body,
        ensure_refer_style as _ensure_refer_style,
        ensure_table_text_style as _ensure_table_text_style,
        load_template_document as _load_template_document,
    )
    from normalize_docx_parts.unsupported_drawing import (  # type: ignore
        replace_unsupported_drawings_or_fallback as _replace_unsupported_drawings_or_fallback,
    )
    from normalize_docx_parts.word_replace import (  # type: ignore
        replace_chart_placeholders as _replace_chart_placeholders,
        replace_image_placeholders as _replace_image_placeholders,
        replace_math_placeholders as _replace_math_placeholders,
    )
    from normalize_docx_parts.xml_extract import (  # type: ignore
        load_numbering as _load_numbering,
        load_rels as _load_rels,
    )


def normalize_docx(input_path: Path, output_path: Path) -> None:
    with zipfile.ZipFile(input_path, "r") as zf:
        doc_xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
        numbering = _load_numbering(zf, NS)
        rels = _load_rels(zf)

        root = ET.fromstring(doc_xml)
        body = root.find("w:body", NS)
        if body is None:
            raise RuntimeError("No document body")

        out = _load_template_document(TEMPLATE_PATH)
        _clear_document_body(out)
        table_text_style = _ensure_table_text_style(out)
        refer_style = _ensure_refer_style(out)

        result = rebuild_document_from_body(
            body=body,
            out=out,
            zf=zf,
            rels=rels,
            numbering=numbering,
            ns=NS,
            refer_style=refer_style,
            table_text_style=table_text_style,
        )
        out.save(output_path)

    if result.chart_placeholder_idx:
        _replace_chart_placeholders(input_path, output_path, result.chart_placeholder_idx)
    if result.image_placeholder_positions:
        _replace_image_placeholders(input_path, output_path, result.image_placeholder_positions)
    if result.math_placeholder_count:
        _replace_math_placeholders(input_path, output_path, result.math_placeholder_count)
    if result.unsupported_drawing_count:
        _replace_unsupported_drawings_or_fallback(
            input_path,
            output_path,
            result.unsupported_drawing_count,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize DOCX: remove styles, keep content")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    normalize_docx(args.input, args.output)


if __name__ == "__main__":
    main()
