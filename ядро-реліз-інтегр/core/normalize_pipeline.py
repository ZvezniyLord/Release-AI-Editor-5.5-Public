from __future__ import annotations

import time
from pathlib import Path

from core.block_pipeline import process_article_blocks
from core.normalize_docx import normalize_docx
from core.normalize_eval import evaluate_docx, write_eval_report
from dashboard_core.io.word_converter import convert_doc_to_docx
from dashboard_core.outputs.json_report_writer import write_json


def normalize_folder(source_folder: Path, output: Path, report: Path, *, write_logs: bool = False) -> None:
    output.mkdir(parents=True, exist_ok=True)
    reports: list[dict] = []
    sources = (
        list(source_folder.glob("*.docx"))
        + list(source_folder.glob("*.doc"))
        + list(source_folder.glob("*.dot"))
        + list(source_folder.glob("*.rtf"))
        + list(source_folder.glob("*.odt"))
    )
    total = len(sources)
    logs_dir = (output / "logs") if write_logs else None
    total_start = time.perf_counter()
    timing_rows: list[dict] = []

    for index, src in enumerate(sorted(sources), start=1):
        out = output / f"{src.stem}.docx"
        file_start = time.perf_counter()
        conv_sec = 0.0
        normalize_sec = 0.0
        blocks_sec = 0.0
        eval_sec = 0.0
        try:
            print(f"[normalize] {index}/{total}")
            print(f"[normalize] file: {src.name}")
            src_docx = src
            converted = False
            if src.suffix.lower() in {".doc", ".dot", ".rtf", ".odt"}:
                print(f"[normalize] convert {src.suffix.lower()} -> .docx: {src.name}")
                conv_start = time.perf_counter()
                src_docx = convert_doc_to_docx(src)
                conv_sec = time.perf_counter() - conv_start
                converted = True

            print(f"[normalize] base normalize: {src_docx.name}")
            normalize_start = time.perf_counter()
            normalize_docx(src_docx, out)
            normalize_sec = time.perf_counter() - normalize_start

            print(f"[normalize] blocks: {out.name}")
            blocks_start = time.perf_counter()
            process_article_blocks(out, logs_dir=logs_dir)
            blocks_sec = time.perf_counter() - blocks_start

            print(f"[normalize] eval: {out.name}")
            eval_start = time.perf_counter()
            item = evaluate_docx(src_docx, out, converted_from=src if converted else None)
            eval_sec = time.perf_counter() - eval_start
            reports.append(item)
        except Exception as exc:
            reports.append({"source": str(src), "error": str(exc)})
        finally:
            total_sec = time.perf_counter() - file_start
            timing_rows.append({
                "source": str(src),
                "convert_sec": round(conv_sec, 3),
                "normalize_sec": round(normalize_sec, 3),
                "blocks_sec": round(blocks_sec, 3),
                "evaluate_sec": round(eval_sec, 3),
                "total_sec": round(total_sec, 3),
            })
            print(
                f"[normalize] timing {src.name}: total={total_sec:.2f}s "
                f"(convert={conv_sec:.2f}s normalize={normalize_sec:.2f}s blocks={blocks_sec:.2f}s eval={eval_sec:.2f}s)"
            )

    write_eval_report(report, reports)
    timings_path = report.with_name("normalize_timings.json")
    write_json(timings_path, timing_rows)
    elapsed_total = time.perf_counter() - total_start
    print(f"[normalize] timing summary: {len(timing_rows)} files, {elapsed_total:.2f}s total, details: {timings_path}")
