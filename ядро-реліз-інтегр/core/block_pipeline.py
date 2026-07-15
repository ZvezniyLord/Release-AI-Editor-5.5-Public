from __future__ import annotations

from pathlib import Path

from core.block_detector import detect_article_blocks, write_block_report
from core.block_handlers.caption_block import process_caption_block
from core.block_handlers.markers_block import process_markers_block


def process_article_blocks(doc_path: Path, logs_dir: Path | None = None) -> None:
    blocks = detect_article_blocks(doc_path)
    write_block_report(doc_path, logs_dir, blocks)
    process_markers_block(doc_path, logs_dir)
    process_caption_block(doc_path, logs_dir)
