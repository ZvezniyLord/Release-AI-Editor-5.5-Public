# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import importlib.util
import shutil
import tempfile
from pathlib import Path


def _load_toc_module():
    root = Path(__file__).resolve().parents[1]
    toc_main = root / "toc_core" / "main.py"
    spec = importlib.util.spec_from_file_location("toc_core_main", toc_main)
    if spec is None or spec.loader is None:
        raise RuntimeError("Не вдалося завантажити toc_core")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy_to_temp(src: Path) -> Path:
    temp_dir = Path(tempfile.gettempdir()) / "toc_core_tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / src.name
    shutil.copy2(src, temp_path)
    return temp_path


def build_toc(input_path: Path, output_path: Path, template_path: Path, manifest_path: Path | None) -> None:
    toc = _load_toc_module()
    temp_doc = _copy_to_temp(input_path)
    try:
        toc.build_toc_document(temp_doc, output_path, template_path, manifest_path)
    finally:
        try:
            temp_doc.unlink(missing_ok=True)
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Додати таблицю змісту (інтегровано)")
    parser.add_argument("input", type=Path, help="DOCX")
    parser.add_argument("--output", type=Path, default=None, help="Вихідний DOCX")
    parser.add_argument("--template", type=Path, required=True, help="Шаблон Table.docx")
    parser.add_argument("--manifest", type=Path, default=None, help="manifest.json (опціонально)")
    args = parser.parse_args()

    doc_path = args.input.resolve()
    if not doc_path.exists():
        raise SystemExit("Файл не знайдено")
    template_path = args.template.resolve()
    if not template_path.exists():
        raise SystemExit(f"Шаблон не знайдено: {template_path}")
    output_path = args.output or doc_path.with_name(f"{doc_path.stem}_зміст{doc_path.suffix}")
    manifest_path = args.manifest.resolve() if args.manifest else None

    build_toc(doc_path, output_path, template_path, manifest_path)
    print(f"Готово: {output_path}")


if __name__ == "__main__":
    main()
