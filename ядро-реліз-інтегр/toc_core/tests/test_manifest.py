# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from manifest_reader import load_free_listeners


def test_manifest_normal(tmp_path: Path):
    matches_path = tmp_path / "matches.json"
    manifest_path = tmp_path / "manifest.json"

    matches = {
        "matches": [
            {"match_method": "free_listener", "authors": ["A", "B"]},
            {"match_method": "free_listener", "title": "C"},
            {"match_method": "other", "authors": ["X"]},
        ]
    }
    matches_path.write_text(json.dumps(matches, ensure_ascii=False), encoding="utf-8")
    manifest_path.write_text(json.dumps({"matches_json_path": str(matches_path)}), encoding="utf-8")

    header, result = load_free_listeners(manifest_path)
    assert header
    assert result == ["A", "B", "C"]


def test_manifest_missing(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"
    header, result = load_free_listeners(manifest_path)
    assert header
    assert result == []


def test_manifest_corrupt(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{bad json", encoding="utf-8")
    header, result = load_free_listeners(manifest_path)
    assert header
    assert result == []
