from __future__ import annotations

from pathlib import Path


def resolve_template_path(explicit: Path | None = None) -> Path | None:
    if explicit is not None:
        return explicit if explicit.exists() else None
    candidates = [
        Path(__file__).resolve().parents[1] / "assets" / "templates" / "Jurnal.dotx",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None
