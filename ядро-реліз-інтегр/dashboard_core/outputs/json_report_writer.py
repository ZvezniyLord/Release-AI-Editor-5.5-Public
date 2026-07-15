from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path


def _to_json_ready(value):
    if is_dataclass(value):
        return _to_json_ready(asdict(value))
    if isinstance(value, dict):
        return {key: _to_json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_to_json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_to_json_ready(payload), ensure_ascii=False, indent=2), encoding="utf-8")
