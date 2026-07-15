from __future__ import annotations

WD_ALIGN_PARAGRAPH_CENTER = 1


def _apply_section_fallback(paragraph) -> None:
    fmt = paragraph.ParagraphFormat
    fmt.LeftIndent = 0
    fmt.FirstLineIndent = 0
    fmt.RightIndent = 0
    fmt.SpaceBefore = 12
    fmt.SpaceAfter = 36
    fmt.SpaceBeforeAuto = False
    fmt.SpaceAfterAuto = False
    fmt.Alignment = WD_ALIGN_PARAGRAPH_CENTER
    try:
        fmt.OutlineLevel = 1
    except Exception:
        pass
    paragraph.Font.Name = "Times New Roman"
    paragraph.Font.Size = 30
    paragraph.Font.Bold = True
    try:
        paragraph.Font.AllCaps = True
    except Exception:
        pass


def _ensure_paragraph_style(document, name: str, base_candidates: list[str]) -> str | None:
    try:
        existing = {str(style.NameLocal): style for style in document.Styles}
    except Exception:
        return None
    normalized = {key.casefold(): key for key in existing}
    if name in existing:
        return name
    resolved = normalized.get(name.casefold())
    if resolved:
        return resolved
    base_style = None
    for candidate in base_candidates:
        if candidate in existing:
            base_style = existing[candidate]
            break
        resolved_candidate = normalized.get(candidate.casefold())
        if resolved_candidate:
            base_style = existing[resolved_candidate]
            break
    try:
        new_style = document.Styles.Add(name, 1)
    except Exception:
        return None
    if base_style is not None:
        try:
            new_style.BaseStyle = base_style.NameLocal
        except Exception:
            pass
    return str(new_style.NameLocal)


def _insert_heading(document, text: str, section_style: str | None) -> None:
    end_range = document.Range(document.Content.End - 1, document.Content.End - 1)
    end_range.InsertAfter(text)
    paragraph = document.Paragraphs.Last.Range
    if section_style:
        paragraph.Style = section_style
    else:
        _apply_section_fallback(paragraph)
    paragraph.InsertParagraphAfter()
