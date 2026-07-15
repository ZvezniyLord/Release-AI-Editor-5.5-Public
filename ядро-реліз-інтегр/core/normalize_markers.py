from __future__ import annotations

from pathlib import Path

from core.normalize_annotation_markers import normalize_annotations
from core.normalize_reference_markers import normalize_references


def apply_markers(doc_path: Path, logs_dir: Path | None = None) -> None:
    write_logs = logs_dir is not None
    normalize_annotations(doc_path, output_path=doc_path, logs_dir=logs_dir, write_logs=write_logs)
    normalize_references(doc_path, output_path=doc_path, logs_dir=logs_dir, write_logs=write_logs)
