# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
import time
from pathlib import Path

import pythoncom
import win32com.client


class WordComError(RuntimeError):
    pass


@dataclass(frozen=True)
class TableStyles:
    section: str = "Tab_SEC"
    authors: str = "Tab_PIP"
    title: str = "Tab_Taitl"


def start_word(attempts: int = 5, delay_sec: float = 2.0):
    pythoncom.CoInitialize()
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            word = win32com.client.DispatchEx("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0
            try:
                word.ScreenUpdating = False
            except Exception:
                pass
            return word
        except Exception as error:
            last_error = error
            time.sleep(delay_sec)
    raise WordComError("Не вдалося запустити Word COM") from last_error


def shutdown_word(word) -> None:
    try:
        if word is not None:
            try:
                word.ScreenUpdating = True
            except Exception:
                pass
            word.Quit()
    finally:
        pythoncom.CoUninitialize()


def open_document(word, path: Path, read_only: bool = False, open_and_repair: bool = False):
    try:
        return word.Documents.Open(
            str(path),
            ConfirmConversions=False,
            ReadOnly=read_only,
            AddToRecentFiles=False,
            OpenAndRepair=open_and_repair,
            Visible=False,
        )
    except Exception as error:
        raise WordComError("Не вдалося відкрити документ у Word COM") from error


def _clean_cell_text(text: str) -> str:
    return (text or "").replace("\r", "").replace("\a", "").strip()


def _row_has_text(row) -> bool:
    try:
        for cell in row.Cells:
            if _clean_cell_text(cell.Range.Text):
                return True
    except Exception:
        return False
    return False


def _count_reserved_tail_rows(table) -> int:
    reserved = 0
    for idx in range(table.Rows.Count, 0, -1):
        if _row_has_text(table.Rows(idx)):
            reserved += 1
        else:
            break
    return reserved


def insert_table_from_template(word, document, template_path: Path):
    try:
        template_doc = open_document(word, template_path, read_only=True)
        template_doc.Tables(1).Range.Copy()
        start_range = document.Range(0, 0)
        start_range.Paste()
        table = document.Tables(1)
        return table, template_doc
    except Exception as error:
        raise WordComError("Не вдалося вставити таблицю з шаблону") from error


def add_page_break_after_table(document, table, page_break_type: int = 7) -> None:
    end_range = document.Range(table.Range.End, table.Range.End)
    end_range.InsertBreak(page_break_type)


def ensure_rows(table, target_row_count: int) -> None:
    while table.Rows.Count < target_row_count:
        table.Rows.Add()


def _clear_table(table) -> None:
    # Keep table formatting but remove existing content/rows.
    for idx in range(table.Rows.Count, 1, -1):
        try:
            table.Rows(idx).Delete()
        except Exception:
            pass
    try:
        for cell in table.Rows(1).Cells:
            cell.Range.Text = ""
    except Exception:
        pass


def fill_table(table, rows, styles: TableStyles) -> None:
    _clear_table(table)
    target_count = max(1, len(rows))
    ensure_rows(table, target_count)

    for index, row in enumerate(rows, start=1):
        row_obj = table.Rows(index)
        cell = row_obj.Cells(2)
        if row.kind == "section":
            cell.Range.Text = row.section
            try:
                cell.Range.Style = styles.section
            except Exception:
                pass
        elif row.kind == "free_listeners_header":
            cell.Range.Text = row.section
            try:
                cell.Range.Style = styles.section
            except Exception:
                pass
        elif row.kind == "item":
            if row.authors:
                cell.Range.Text = f"{row.authors}\n{row.title}".strip()
                try:
                    cell.Range.Paragraphs(1).Range.Style = styles.authors
                except Exception:
                    pass
                try:
                    if cell.Range.Paragraphs.Count >= 2:
                        cell.Range.Paragraphs(2).Range.Style = styles.title
                except Exception:
                    pass
            else:
                cell.Range.Text = row.title
                try:
                    cell.Range.Style = styles.title
                except Exception:
                    pass
        elif row.kind == "free_listeners":
            cell.Range.Text = row.free_listeners
            try:
                cell.Range.Style = styles.authors
            except Exception:
                pass


def extract_outline_from_word(document) -> list[tuple[int, str]]:
    items: list[tuple[int, str]] = []
    total = document.Paragraphs.Count
    for idx in range(1, total + 1):
        para = document.Paragraphs(idx)
        text = (para.Range.Text or "").replace("\r", "").strip()
        if not text:
            continue
        try:
            level = int(para.OutlineLevel)
        except Exception:
            continue
        if level in (1, 2, 3):
            items.append((level, text))
    return items
