from __future__ import annotations

from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph


def is_empty_paragraph(para: Paragraph) -> bool:
    if (para.text or "").strip():
        return False
    try:
        for node in para._element.iter():
            tag = str(node.tag)
            if tag.endswith("}drawing") or tag.endswith("}pict") or tag.endswith("}object"):
                return False
    except Exception:
        pass
    return True


def remove_paragraph(para: Paragraph) -> None:
    element = para._element
    parent = element.getparent()
    if parent is not None:
        parent.remove(element)


def insert_empty_after(para: Paragraph) -> Paragraph:
    new_p = OxmlElement("w:p")
    para._element.addnext(new_p)
    return Paragraph(new_p, para._parent)


def ensure_single_empty_around(para: Paragraph) -> None:
    prev = para._element.getprevious()
    if prev is None:
        para.insert_paragraph_before("")
    else:
        prev_para = Paragraph(prev, para._parent)
        if not is_empty_paragraph(prev_para):
            para.insert_paragraph_before("")
        else:
            runner = prev_para
            while True:
                prior = runner._element.getprevious()
                if prior is None:
                    break
                prior_para = Paragraph(prior, para._parent)
                if not is_empty_paragraph(prior_para):
                    break
                remove_paragraph(prior_para)
                runner = Paragraph(runner._element.getprevious(), para._parent)

    next_el = para._element.getnext()
    if next_el is None:
        insert_empty_after(para)
    else:
        next_para = Paragraph(next_el, para._parent)
        if not is_empty_paragraph(next_para):
            insert_empty_after(para)
        else:
            runner = next_para
            while True:
                nxt = runner._element.getnext()
                if nxt is None:
                    break
                nxt_para = Paragraph(nxt, para._parent)
                if not is_empty_paragraph(nxt_para):
                    break
                remove_paragraph(nxt_para)
                runner = Paragraph(runner._element.getnext(), para._parent)
