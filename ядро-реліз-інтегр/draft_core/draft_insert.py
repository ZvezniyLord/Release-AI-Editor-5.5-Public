from __future__ import annotations

from pathlib import Path

from .constants import WORD_COLLAPSE_END, WORD_PAGE_BREAK

WD_ALIGN_PARAGRAPH_CENTER = 1


def _insert_document(document, source_path: Path, add_page_break: bool) -> tuple[int, int] | None:
    if not source_path.exists():
        return None
    start_pos = document.Content.End - 1
    end_range = document.Range(start_pos, start_pos)
    end_range.Collapse(WORD_COLLAPSE_END)
    end_range.InsertFile(str(source_path))
    end_pos = document.Content.End - 1
    tail_range = document.Range(document.Content.End - 1, document.Content.End - 1)
    tail_range.InsertParagraphAfter()
    if add_page_break:
        tail_range = document.Range(document.Content.End - 1, document.Content.End - 1)
        tail_range.InsertBreak(WORD_PAGE_BREAK)
    return start_pos, end_pos


def _center_media_in_range(document, start_pos: int, end_pos: int) -> None:
    try:
        rng = document.Range(start_pos, end_pos)
    except Exception:
        return
    # Center tables and clear paragraph indents
    try:
        tables = rng.Tables
    except Exception:
        tables = []
    for table in tables:
        try:
            try:
                table.Rows.Alignment = WD_ALIGN_PARAGRAPH_CENTER
            except Exception:
                pass
            try:
                table.Alignment = WD_ALIGN_PARAGRAPH_CENTER
            except Exception:
                pass
            try:
                table.LeftIndent = 0
            except Exception:
                pass
            table.Range.ParagraphFormat.Alignment = WD_ALIGN_PARAGRAPH_CENTER
            table.Range.ParagraphFormat.LeftIndent = 0
            table.Range.ParagraphFormat.FirstLineIndent = 0
        except Exception:
            pass

    # Center inline pictures/shapes
    try:
        inlines = rng.InlineShapes
    except Exception:
        inlines = []
    for shape in inlines:
        try:
            pr = shape.Range.ParagraphFormat
            pr.Alignment = WD_ALIGN_PARAGRAPH_CENTER
            pr.LeftIndent = 0
            pr.FirstLineIndent = 0
        except Exception:
            pass
