from __future__ import annotations

from dataclasses import dataclass
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class ListFmt:
    fmt: str
    lvl: int


def int_to_roman(n: int) -> str:
    vals = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]
    out: list[str] = []
    for v, s in vals:
        while n >= v:
            out.append(s)
            n -= v
    return "".join(out)


def int_to_alpha(n: int) -> str:
    # 1->a, 2->b ... 26->z, 27->aa
    out: list[str] = []
    n0 = n
    while n0 > 0:
        n0 -= 1
        out.append(chr(ord("a") + (n0 % 26)))
        n0 //= 26
    return "".join(reversed(out))


def paragraph_list_info(
    p: ET.Element,
    numbering: dict[tuple[str, int], str],
    ns: dict[str, str],
) -> ListFmt | None:
    ppr = p.find("w:pPr", ns)
    if ppr is None:
        return None
    numpr = ppr.find("w:numPr", ns)
    if numpr is None:
        return None
    num_id = numpr.find("w:numId", ns)
    ilvl = numpr.find("w:ilvl", ns)
    if num_id is None or ilvl is None:
        return None
    num_val = num_id.get(f"{{{ns['w']}}}val")
    ilvl_val = ilvl.get(f"{{{ns['w']}}}val")
    if num_val is None or ilvl_val is None:
        return None
    try:
        lvl = int(ilvl_val)
    except Exception:
        return None
    fmt = numbering.get((num_val, lvl), "")
    return ListFmt(fmt=fmt, lvl=lvl)


def next_list_prefix(
    list_info: ListFmt,
    counters: dict[tuple[str, int], int],
) -> tuple[str, str]:
    key = (list_info.fmt, list_info.lvl)
    counters[key] = counters.get(key, 0) + 1
    current = counters[key]
    prefix = ""
    if list_info.fmt in {"bullet"}:
        prefix = "\u2022 "
    elif list_info.fmt in {"decimal"}:
        prefix = f"{current}. "
    elif list_info.fmt in {"lowerLetter"}:
        prefix = f"{int_to_alpha(current)}) "
    elif list_info.fmt in {"upperLetter"}:
        prefix = f"{int_to_alpha(current).upper()}) "
    elif list_info.fmt in {"lowerRoman"}:
        prefix = f"{int_to_roman(current).lower()}. "
    elif list_info.fmt in {"upperRoman"}:
        prefix = f"{int_to_roman(current)}. "
    indent = "  " * list_info.lvl
    return indent, prefix
