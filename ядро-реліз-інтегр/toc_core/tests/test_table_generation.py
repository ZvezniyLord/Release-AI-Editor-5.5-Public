# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from table_builder import build_rows
from outline_parser import Section, SectionItem


def test_table_rows():
    sections = [
        Section(name="S1", items=[SectionItem(authors="A1", title="T1")]),
        Section(name="S2", items=[SectionItem(authors="A2", title="T2"), SectionItem(authors="A3", title="T3")]),
    ]
    rows = build_rows(sections, free_listeners=["X", "Y"])
    assert rows[0].kind == "section" and rows[0].section == "S1"
    assert rows[1].kind == "item" and rows[1].authors == "A1" and rows[1].title == "T1"
    assert rows[2].kind == "section" and rows[2].section == "S2"
    assert rows[-1].kind == "free_listeners"
