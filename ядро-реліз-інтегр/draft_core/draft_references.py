from __future__ import annotations

import win32com.client


def _restart_reference_numbering_in_range(document, start_pos: int, end_pos: int) -> None:
    headings = {"СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:", "REFERENCES:"}
    try:
        constants = win32com.client.constants
    except Exception:
        constants = None
    wdListNoNumbering = 0
    apply_to_forward = getattr(constants, "wdListApplyToThisPointForward", 2)
    apply_to_selection = getattr(constants, "wdListApplyToSelection", 0)
    default_behavior = getattr(constants, "wdWord10ListBehavior", 2)

    try:
        rng = document.Range(start_pos, end_pos)
        paragraphs = rng.Paragraphs
        total = int(paragraphs.Count)
    except Exception:
        return

    for idx in range(1, total + 1):
        try:
            para = paragraphs(idx)
            text = para.Range.Text.strip("\r\x07 ").strip()
        except Exception:
            continue
        if text not in headings:
            continue
        for j in range(idx + 1, total + 1):
            try:
                next_para = paragraphs(j)
                next_text = next_para.Range.Text.strip("\r\x07 ").strip()
            except Exception:
                break
            if not next_text:
                continue
            if next_text in headings:
                break
            try:
                list_type = int(next_para.Range.ListFormat.ListType)
            except Exception:
                list_type = wdListNoNumbering
            if list_type == wdListNoNumbering:
                break
            try:
                template = next_para.Range.ListFormat.ListTemplate
                # Find the last paragraph that still belongs to this list block
                last_para = next_para
                for k in range(j + 1, total + 1):
                    try:
                        cand = paragraphs(k)
                        cand_text = cand.Range.Text.strip("\r\x07 ").strip()
                    except Exception:
                        break
                    if not cand_text:
                        break
                    if cand_text in headings:
                        break
                    try:
                        cand_type = int(cand.Range.ListFormat.ListType)
                    except Exception:
                        cand_type = wdListNoNumbering
                    if cand_type == wdListNoNumbering:
                        break
                    last_para = cand
                try:
                    rng = document.Range(next_para.Range.Start, last_para.Range.End)
                    rng.ListFormat.ApplyListTemplateWithLevel(
                        template,
                        False,
                        apply_to_selection,
                        default_behavior,
                    )
                except Exception:
                    next_para.Range.ListFormat.ApplyListTemplateWithLevel(
                        template,
                        False,
                        apply_to_forward,
                        default_behavior,
                    )
            except Exception:
                pass
            break
