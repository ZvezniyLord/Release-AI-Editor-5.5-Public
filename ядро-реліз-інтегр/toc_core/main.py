# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from docx import Document
    _DOCX_AVAILABLE = True
except Exception:
    _DOCX_AVAILABLE = False

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from outline_parser import parse_outline, build_sections, OutlineItem
from manifest_reader import load_free_listeners
from table_builder import build_rows
from word_com import start_word, shutdown_word, open_document, insert_table_from_template, add_page_break_after_table, fill_table, TableStyles, WordComError, extract_outline_from_word
from gui import run_gui

DEFAULT_TEMPLATE = ROOT.parent / "assets" / "templates" / "Table.docx"


def _canonical_style(name: str) -> str:
    return "".join(ch for ch in name.casefold() if ch.isalnum())


def detect_table_styles(template_path: Path) -> TableStyles:
    if not _DOCX_AVAILABLE:
        return TableStyles()
    try:
        doc = Document(str(template_path))
    except Exception:
        return TableStyles()
    style_names = [s.name for s in doc.styles if s and s.name]
    canonical = {_canonical_style(name): name for name in style_names}

    def pick(default_name: str) -> str:
        key = _canonical_style(default_name)
        if key in canonical:
            return canonical[key]
        return default_name

    return TableStyles(
        section=pick("Tab_SEC"),
        authors=pick("Tab_PIP"),
        title=pick("Tab_Taitl"),
    )


def build_toc_document(doc_path: Path, output_path: Path, template_path: Path, manifest_path: Path | None) -> None:
    print(f"[toc] parse outline: {doc_path}", flush=True)
    outline = parse_outline(doc_path)
    levels = {item.level for item in outline}
    need_fallback = not {1, 2, 3}.issubset(levels)
    sections = build_sections(outline)
    free_listener_header, free_listeners = load_free_listeners(manifest_path)
    rows = build_rows(sections, free_listeners, free_listener_header=free_listener_header)

    styles = detect_table_styles(template_path)
    word = None
    document = None
    template_doc = None
    try:
        word = start_word()
        try:
            document = open_document(word, doc_path, read_only=False)
        except WordComError:
            document = open_document(word, doc_path, read_only=False, open_and_repair=True)

        if need_fallback:
            print("[toc] fallback to Word COM outline", flush=True)
            outline_rows = extract_outline_from_word(document)
            outline = [OutlineItem(level=lvl, text=txt) for lvl, txt in outline_rows]
            sections = build_sections(outline)
            rows = build_rows(sections, free_listeners, free_listener_header=free_listener_header)

        table, template_doc = insert_table_from_template(word, document, template_path)
        add_page_break_after_table(document, table)
        fill_table(table, rows, styles)
        document.SaveAs2(str(output_path), FileFormat=16)
    finally:
        if template_doc is not None:
            template_doc.Close(False)
        if document is not None:
            document.Close(False)
        shutdown_word(word)


def main() -> None:
    parser = argparse.ArgumentParser(description="GPT Super Табел: додати таблицю змісту")
    parser.add_argument("input", type=Path, nargs="?", default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--template", type=Path, default=None)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--cli", action="store_true")
    args = parser.parse_args()

    if not args.cli:
        run_gui(build_toc_document, default_template=DEFAULT_TEMPLATE)
        return

    if args.input is None:
        value = input("Вкажи шлях до документа: ").strip().strip('"')
        if not value:
            raise SystemExit("Порожній шлях")
        doc_path = Path(value)
    else:
        doc_path = Path(str(args.input).strip().strip('"'))

    if not doc_path.exists():
        raise SystemExit("Файл не знайдено")

    template_path = args.template or DEFAULT_TEMPLATE
    if not template_path.exists():
        raise SystemExit(f"Шаблон не знайдено: {template_path}")

    output_path = args.output or doc_path.with_name(f"{doc_path.stem}_зміст{doc_path.suffix}")
    build_toc_document(doc_path, output_path, template_path, args.manifest)
    print(f"Готово: {output_path}")


if __name__ == "__main__":
    main()
