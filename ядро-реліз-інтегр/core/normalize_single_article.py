from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.block_handlers.header_block import process_header_block
from core.block_pipeline import process_article_blocks
from core.normalize_docx import normalize_docx
from core.title_style_apply import normalize_titles_docx
from core.block_handlers.order_block import enforce_primary_order_with_title


def normalize_single_article(input_path: Path, output_path: Path, title: str) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalize_docx(input_path, output_path)
    process_article_blocks(output_path)
    enforce_primary_order_with_title(output_path, title)
    report_path = output_path.parent.parent / "shapka_report.json"
    process_header_block(output_path.parent, report_path)
    normalize_titles_docx(
        output_path,
        align_titles=True,
        titles_override=[title],
        use_heuristics=False,
        run_dir=output_path.parent.parent if output_path.parent.parent.exists() else None,
        write_report=False,
    )
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Нормалізувати один документ статті")
    parser.add_argument("input", type=Path, help="Вхідний .docx")
    parser.add_argument("--title", required=True, help="Назва статті (вводить оператор)")
    parser.add_argument("--output", type=Path, default=None, help="Шлях для нормалізованого файлу")
    args = parser.parse_args()

    input_path = args.input.resolve()
    if not input_path.exists():
        raise SystemExit(f"Файл не знайдено: {input_path}")

    title = (args.title or "").strip()
    if not title:
        raise SystemExit("Назва статті порожня.")

    output_path = args.output
    if output_path is None:
        output_path = input_path.with_suffix(".docx")
    output_path = output_path.resolve()

    normalize_single_article(input_path, output_path, title)
    print(f"[normalize-single] done: {output_path}")


if __name__ == "__main__":
    main()
