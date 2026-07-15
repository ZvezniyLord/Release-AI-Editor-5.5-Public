from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.normalize_pipeline import normalize_folder


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize all DOCX in folder")
    parser.add_argument("source_folder", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--debug-logs", action="store_true", help="Зберігати технічні per-file логи у output/logs")
    args = parser.parse_args()

    normalize_folder(args.source_folder, args.output, args.report, write_logs=bool(args.debug_logs))


if __name__ == "__main__":
    main()
