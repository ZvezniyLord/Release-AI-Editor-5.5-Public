from __future__ import annotations

from pathlib import Path

from core.normalize_markers import apply_markers


def process_markers_block(doc_path: Path, logs_dir: Path | None = None) -> None:
    apply_markers(doc_path, logs_dir=logs_dir)
