from __future__ import annotations

from pathlib import Path

from core.normalize_caption_layout import normalize_caption_layout


def process_caption_block(doc_path: Path, logs_dir: Path | None = None) -> None:
    _ = logs_dir
    normalize_caption_layout(doc_path)
