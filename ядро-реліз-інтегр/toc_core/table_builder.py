# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
try:
    from .outline_parser import Section
except Exception:
    from outline_parser import Section


@dataclass(frozen=True)
class TableRow:
    kind: str  # "section" | "item" | "free_listeners_header" | "free_listeners"
    section: str = ""
    authors: str = ""
    title: str = ""
    free_listeners: str = ""


def build_rows(
    sections: Iterable[Section],
    free_listeners: list[str] | None = None,
    *,
    free_listener_header: str = "",
) -> list[TableRow]:
    rows: list[TableRow] = []
    for section in sections:
        rows.append(TableRow(kind="section", section=section.name))
        for item in section.items:
            rows.append(TableRow(kind="item", authors=item.authors, title=item.title))
    if free_listeners:
        header = free_listener_header.strip()
        if header:
            rows.append(TableRow(kind="free_listeners_header", section=header))
        rows.append(TableRow(kind="free_listeners", free_listeners=", ".join(free_listeners)))
    return rows
