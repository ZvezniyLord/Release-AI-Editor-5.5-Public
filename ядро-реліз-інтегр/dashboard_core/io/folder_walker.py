from __future__ import annotations

import os
from pathlib import Path

from ..constants import SUPPORTED_WORD_EXTENSIONS


def collect_word_files(base_dir: Path, *, cancel_event=None, log_callback=None) -> list[Path]:
    files: list[Path] = []
    scanned = 0
    for root, _dirs, filenames in os.walk(base_dir, followlinks=False):
        if cancel_event is not None and cancel_event.is_set():
            break
        for name in filenames:
            if cancel_event is not None and cancel_event.is_set():
                break
            scanned += 1
            path = Path(root) / name
            if path.suffix.lower() in SUPPORTED_WORD_EXTENSIONS:
                files.append(path)
            if log_callback and scanned % 200 == 0:
                log_callback(f"[scan] scanned files: {scanned}")
    files.sort()
    return files
