# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

import pythoncom
import win32com.client

PROJECT_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = PROJECT_DIR / "assets" / "templates" / "Jurnal.dotx"

WD_STYLE_TYPE_TABLE = 3
WD_LINE_SPACE_MULTIPLE = 5


def _safe_lines_to_points(app, value: float) -> float:
    try:
        return app.LinesToPoints(value)
    except Exception:
        return 14 * value


def main() -> None:
    template = TEMPLATE_PATH
    if len(sys.argv) > 1:
        template = Path(sys.argv[1]).resolve()
    if not template.exists():
        raise SystemExit(f"Template not found: {template}")

    pythoncom.CoInitialize()
    word = None
    document = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        document = word.Documents.Open(
            str(template),
            ConfirmConversions=False,
            ReadOnly=False,
            AddToRecentFiles=False,
            Visible=False,
        )

        # Ensure Table Grid exists
        try:
            style = document.Styles("Table Grid")
        except Exception:
            style = document.Styles.Add("Table Grid", WD_STYLE_TYPE_TABLE)

        # Set table style defaults
        try:
            style.ParagraphFormat.LeftIndent = 0
            style.ParagraphFormat.RightIndent = 0
            style.ParagraphFormat.FirstLineIndent = 0
            style.ParagraphFormat.SpaceBefore = 0
            style.ParagraphFormat.SpaceAfter = 0
            style.ParagraphFormat.SpaceBeforeAuto = False
            style.ParagraphFormat.SpaceAfterAuto = False
            style.ParagraphFormat.LineSpacingRule = WD_LINE_SPACE_MULTIPLE
            style.ParagraphFormat.LineSpacing = _safe_lines_to_points(word, 1.15)
        except Exception:
            pass

        try:
            style.Font.Name = "Times New Roman"
            style.Font.Size = 12
        except Exception:
            pass

        # Try to enable borders for the style
        try:
            style.Table.Borders.Enable = True
        except Exception:
            pass

        # Make it default for new tables if supported
        try:
            document.DefaultTableStyle = "Table Grid"
        except Exception:
            pass

        document.Save()
        print(f"[ok] Updated table style in template: {template}")
    finally:
        if document is not None:
            document.Close(False)
        if word is not None:
            word.Quit()
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    main()
