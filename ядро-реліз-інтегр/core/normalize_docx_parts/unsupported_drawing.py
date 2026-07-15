from __future__ import annotations

import os
from pathlib import Path


def _word_visible() -> bool:
    return os.getenv("WORD_COM_VISIBLE", "").strip().lower() in {"1", "true", "yes", "y"}


def _fallback_text(source_path: Path) -> str:
    return (
        "[РќР•РџР•Р Р•РќР•РЎР•РќРР™ Р“Р РђР¤Р†Р§РќРР™ Р‘Р›РћРљ: "
        f"РґРёРІ. РѕСЂРёРіС–РЅР°Р» СЃС‚Р°С‚С‚С– РґР»СЏ СЂСѓС‡РЅРѕРіРѕ РїРµСЂРµРЅРѕСЃСѓ: {source_path}]"
    )


def _collect_source_shapes(src_doc) -> list:
    shapes: list = []
    try:
        total = int(src_doc.Shapes.Count)
    except Exception:
        total = 0
    for i in range(1, total + 1):
        try:
            shp = src_doc.Shapes(i)
        except Exception:
            continue
        has_chart = False
        try:
            has_chart = bool(shp.HasChart)
        except Exception:
            pass
        if has_chart:
            continue
        has_smartart = False
        try:
            _ = shp.SmartArt
            has_smartart = True
        except Exception:
            has_smartart = False
        if has_smartart:
            shapes.append(shp)
    if shapes:
        return shapes

    # Fallback: non-chart floating shapes in source order.
    for i in range(1, total + 1):
        try:
            shp = src_doc.Shapes(i)
        except Exception:
            continue
        has_chart = False
        try:
            has_chart = bool(shp.HasChart)
        except Exception:
            pass
        if not has_chart:
            shapes.append(shp)
    return shapes


def replace_unsupported_drawings_or_fallback(input_path: Path, output_path: Path, count: int) -> None:
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

        src_shapes = _collect_source_shapes(src_doc)
        constants = win32com.client.constants
        wdFindStop = getattr(constants, "wdFindStop", 0)
        wdColorRed = getattr(constants, "wdColorRed", 255)

        for idx in range(1, count + 1):
            token = f"<<UNSUPPORTED_DRAWING_{idx}>>"
            rng = out_doc.Range()
            find = rng.Find
            find.Text = token
            find.Wrap = wdFindStop
            if not find.Execute():
                continue

            pasted = False
            if idx - 1 < len(src_shapes):
                try:
                    src_doc.Activate()
                    src_shapes[idx - 1].Select()
                    word.Selection.Copy()
                    out_doc.Activate()
                    rng.Text = ""
                    rng.Select()
                    word.Selection.Paste()
                    pasted = True
                except Exception:
                    pasted = False
            if not pasted:
                try:
                    rng.Text = _fallback_text(input_path)
                    try:
                        rng.Font.Color = wdColorRed
                        rng.Font.Bold = 1
                    except Exception:
                        pass
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
