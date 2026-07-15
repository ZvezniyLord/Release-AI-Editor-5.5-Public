from __future__ import annotations

import argparse
import os
from pathlib import Path

from core.title_style_apply import normalize_titles_docx


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deprecated: use normalize_titles.py (titles only)."
    )
    parser.add_argument("draft", type=Path, help="Draft docx")
    parser.add_argument("--output", type=Path, default=None, help="Output docx (copy)")
    parser.add_argument("--skip-titles", action="store_true", help="Не застосовувати стиль Назва1")
    parser.add_argument("--skip-authors", action="store_true", help="(ignored) автори винесені в окремий скрипт")
    parser.add_argument("--align-titles", action="store_true", help="Вирівняти назви через підтвердження")
    parser.add_argument("--align-threshold", type=float, default=0.9, help="Поріг схожості")
    parser.add_argument("--align-auto", action="store_true", help="Автоприйняття вирівнювання")
    args = parser.parse_args()

    if not args.draft.exists():
        raise SystemExit("Draft not found")
    if args.skip_titles:
        return
    out = normalize_titles_docx(
        args.draft,
        output_path=args.output,
        align_titles=args.align_titles,
        align_threshold=args.align_threshold,
        align_auto=args.align_auto,
    )
    try:
        os.startfile(str(out))
    except Exception:
        pass


if __name__ == "__main__":
    main()
