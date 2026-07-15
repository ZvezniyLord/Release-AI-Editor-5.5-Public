from __future__ import annotations

import os
from pathlib import Path


def _word_visible() -> bool:
    return os.getenv("WORD_COM_VISIBLE", "").strip().lower() in {"1", "true", "yes", "y"}


def replace_chart_placeholders(input_path: Path, output_path: Path, count: int) -> None:
    try:
        import pythoncom
        import win32com.client
    except Exception:
        return

    pythoncom.CoInitialize()
    word = None
    src_doc = None
    out_doc = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = bool(_word_visible())
        word.DisplayAlerts = 0
        src_doc = word.Documents.Open(str(input_path), ReadOnly=True, AddToRecentFiles=False)
        out_doc = word.Documents.Open(str(output_path), ReadOnly=False, AddToRecentFiles=False)
        src_total = int(src_doc.InlineShapes.Count)
        total = min(count, src_total)
        constants = win32com.client.constants
        wdFindStop = getattr(constants, "wdFindStop", 0)
        for idx in range(1, total + 1):
            token = f"<<CHART_PLACEHOLDER_{idx}>>"
            try:
                src_shape = src_doc.InlineShapes(idx)
            except Exception:
                continue
            try:
                has_chart = bool(src_shape.HasChart)
            except Exception:
                has_chart = False
            if not has_chart:
                continue
            rng = out_doc.Range()
            find = rng.Find
            find.Text = token
            find.Wrap = wdFindStop
            if not find.Execute():
                continue
            try:
                rng.Text = ""
            except Exception:
                pass
            try:
                src_shape.Range.Copy()
                rng.Paste()
            except Exception:
                try:
                    src_doc.Activate()
                    src_shape.Select()
                    word.Selection.Copy()
                    out_doc.Activate()
                    rng.Select()
                    word.Selection.Paste()
                except Exception:
                    pass
        out_doc.Save()
    finally:
        if out_doc is not None:
            out_doc.Close(False)
        if src_doc is not None:
            src_doc.Close(False)
        if word is not None:
            word.Quit()
        pythoncom.CoUninitialize()


def replace_image_placeholders(input_path: Path, output_path: Path, positions: list[int]) -> None:
    if not positions:
        return
    try:
        import pythoncom
        import win32com.client
    except Exception:
        return

    pythoncom.CoInitialize()
    word = None
    src_doc = None
    out_doc = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = bool(_word_visible())
        word.DisplayAlerts = 0
        src_doc = word.Documents.Open(str(input_path), ReadOnly=True, AddToRecentFiles=False)
        out_doc = word.Documents.Open(str(output_path), ReadOnly=False, AddToRecentFiles=False)

        src_shapes = []
        for i in range(1, int(src_doc.InlineShapes.Count) + 1):
            try:
                ish = src_doc.InlineShapes(i)
            except Exception:
                continue
            try:
                if bool(ish.HasChart):
                    continue
            except Exception:
                pass
            src_shapes.append(ish)

        constants = win32com.client.constants
        wdFindStop = getattr(constants, "wdFindStop", 0)

        for idx, pos in enumerate(positions, start=1):
            if pos - 1 >= len(src_shapes):
                continue
            token = f"<<IMG_PLACEHOLDER_{idx}>>"
            rng = out_doc.Range()
            find = rng.Find
            find.Text = token
            find.Wrap = wdFindStop
            if not find.Execute():
                continue
            try:
                rng.Text = ""
            except Exception:
                pass
            try:
                src_shapes[pos - 1].Range.Copy()
                rng.Paste()
            except Exception:
                try:
                    src_doc.Activate()
                    src_shapes[pos - 1].Select()
                    word.Selection.Copy()
                    out_doc.Activate()
                    rng.Select()
                    word.Selection.Paste()
                except Exception:
                    pass
        out_doc.Save()
    finally:
        if out_doc is not None:
            out_doc.Close(False)
        if src_doc is not None:
            src_doc.Close(False)
        if word is not None:
            word.Quit()
        pythoncom.CoUninitialize()


def replace_math_placeholders(input_path: Path, output_path: Path, count: int) -> None:
    if count <= 0:
        return
    try:
        import pythoncom
        import win32com.client
    except Exception:
        return

    pythoncom.CoInitialize()
    word = None
    src_doc = None
    out_doc = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = bool(_word_visible())
        word.DisplayAlerts = 0
        src_doc = word.Documents.Open(str(input_path), ReadOnly=True, AddToRecentFiles=False)
        out_doc = word.Documents.Open(str(output_path), ReadOnly=False, AddToRecentFiles=False)
        constants = win32com.client.constants
        wdFindStop = getattr(constants, "wdFindStop", 0)
        total = min(count, int(src_doc.OMaths.Count))

        for idx in range(1, total + 1):
            token = f"<<OMATH_PLACEHOLDER_{idx}>>"
            rng = out_doc.Range()
            find = rng.Find
            find.Text = token
            find.Wrap = wdFindStop
            if not find.Execute():
                continue
            try:
                rng.Text = ""
            except Exception:
                pass
            try:
                src_doc.OMaths(idx).Range.Copy()
                rng.Paste()
            except Exception:
                try:
                    rng.Text = src_doc.OMaths(idx).Range.Text
                except Exception:
                    pass
        out_doc.Save()
    finally:
        if out_doc is not None:
            out_doc.Close(False)
        if src_doc is not None:
            src_doc.Close(False)
        if word is not None:
            word.Quit()
        pythoncom.CoUninitialize()
