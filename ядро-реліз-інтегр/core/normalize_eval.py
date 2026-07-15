from __future__ import annotations

from pathlib import Path

from core.eval_docx import eval_docx, write_report


def evaluate_docx(before: Path, after: Path, *, converted_from: Path | None = None) -> dict:
    report = eval_docx(before, after)
    item: dict[str, object] = {"source": str(before), "output": str(after), "report": report}
    if converted_from is not None:
        item["converted_from"] = str(converted_from)
    return item


def write_eval_report(path: Path, items: list[dict]) -> None:
    write_report(path, {"items": items})
