from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.normalize_folder import main as normalize_folder_main
from core.title_style_apply import normalize_titles_docx
from core.dashboard_update import update_dashboard_from_run
from core.block_handlers.header_block import process_header_block
from core.block_handlers.order_block import enforce_primary_order_with_title


def _update_matches_cleaned_paths(run_dir: Path, output_dir: Path) -> dict:
    matches_path = run_dir / "matches.json"
    if not matches_path.exists():
        return {"updated": 0, "missing": 0, "total": 0}
    try:
        raw = json.loads(matches_path.read_text(encoding="utf-8"))
    except Exception:
        return {"updated": 0, "missing": 0, "total": 0}
    if not isinstance(raw, list):
        return {"updated": 0, "missing": 0, "total": 0}

    updated = 0
    missing = 0
    for item in raw:
        if not isinstance(item, dict):
            continue
        if item.get("match_method") in {"missing", "missing_source_file", "free_listener"}:
            continue
        candidate = item.get("relocated_path") or item.get("matched_path") or ""
        if not candidate:
            continue
        stem = Path(candidate).stem
        target = output_dir / f"{stem}.docx"
        if target.exists():
            item["cleaned_path"] = str(target)
            updated += 1
            continue
        alt = output_dir / Path(candidate).name
        if alt.exists():
            item["cleaned_path"] = str(alt)
            updated += 1
        else:
            missing += 1

    matches_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"updated": updated, "missing": missing, "total": len(raw)}


def _apply_titles_to_normalized(run_dir: Path, output_dir: Path, *, write_logs: bool = False) -> dict:
    matches_path = run_dir / "matches.json"
    if not matches_path.exists():
        return {"processed": 0, "updated": 0, "errors": []}
    try:
        data = json.loads(matches_path.read_text(encoding="utf-8"))
    except Exception:
        return {"processed": 0, "updated": 0, "errors": ["matches_read_failed"]}
    if not isinstance(data, list):
        return {"processed": 0, "updated": 0, "errors": ["matches_format_invalid"]}
    logs_dir = (output_dir / "logs") if write_logs else None
    processed = 0
    updated = 0
    errors: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        title = (item.get("title") or "").strip()
        if not title:
            continue
        path = item.get("cleaned_path") or item.get("relocated_path") or item.get("matched_path")
        if not path:
            continue
        doc_path = Path(path)
        if not doc_path.exists():
            # try with normalized output dir
            alt = output_dir / f"{doc_path.stem}.docx"
            if alt.exists():
                doc_path = alt
            else:
                continue
        processed += 1
        try:
            # На етапі нормалізації статей запускаємо інтерактивне вирівнювання
            # конкретної назви (тільки для цієї статті).
            normalize_titles_docx(
                doc_path,
                align_titles=True,
                logs_dir=logs_dir,
                titles_override=[title],
                use_heuristics=False,
                run_dir=run_dir,
                write_report=write_logs,
            )
            updated += 1
        except Exception:
            errors.append({"file": str(doc_path), "title": title, "error": "title_align_failed"})
            continue
    return {"processed": processed, "updated": updated, "errors": errors}


def _apply_header_block(output_dir: Path, run_dir: Path) -> None:
    if not output_dir.exists():
        return
    report_path = run_dir / "shapka_report.json"
    print(f"[normalize] header block (shapka): {output_dir}")
    process_header_block(output_dir, report_path)


def _enforce_primary_order(run_dir: Path, output_dir: Path, *, write_logs: bool = False) -> dict:
    matches_path = run_dir / "matches.json"
    if not matches_path.exists():
        return {"checked": 0, "changed": 0, "items": []}
    try:
        data = json.loads(matches_path.read_text(encoding="utf-8"))
    except Exception:
        return {"checked": 0, "changed": 0, "items": [], "error": "matches_read_failed"}
    if not isinstance(data, list):
        return {"checked": 0, "changed": 0, "items": [], "error": "matches_format_invalid"}

    changed = 0
    checked = 0
    logs_dir = (output_dir / "logs") if write_logs else None
    items: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        title = (item.get("title") or "").strip()
        if not title:
            continue
        path = item.get("cleaned_path") or item.get("relocated_path") or item.get("matched_path")
        if not path:
            continue
        doc_path = Path(path)
        if not doc_path.exists():
            alt = output_dir / f"{doc_path.stem}.docx"
            if alt.exists():
                doc_path = alt
            else:
                continue
        checked += 1
        result = enforce_primary_order_with_title(doc_path, title, logs_dir=logs_dir)
        items.append({"file": str(doc_path), **result})
        if result.get("changed"):
            changed += 1
            print(f"[normalize] block-order fixed: {doc_path.name}")

    if checked:
        print(f"[normalize] block-order checked: {checked}, fixed: {changed}")
    return {"checked": checked, "changed": changed, "items": items}


def _read_json(path: Path) -> object:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_consolidated_log(
    run_dir: Path,
    *,
    source_dir: Path,
    output_dir: Path,
    report_path: Path,
    update_matches_stats: dict,
    title_stats: dict,
    order_stats: dict,
    stage_sec: dict[str, float],
    debug_logs: bool,
) -> Path:
    timings_path = report_path.with_name("normalize_timings.json")
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "source_dir": str(source_dir),
        "output_dir": str(output_dir),
        "report_path": str(report_path),
        "timings_path": str(timings_path),
        "debug_logs": bool(debug_logs),
        "stage_sec": stage_sec,
        "update_matches": update_matches_stats,
        "title_align": title_stats,
        "order_block": order_stats,
        "eval_report": _read_json(report_path),
        "timings": _read_json(timings_path),
    }
    out = run_dir / "normalize_debug.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main() -> None:
    total_start = time.perf_counter()
    parser = argparse.ArgumentParser(description="Нормалізувати статті у папці run")
    parser.add_argument("run_dir", type=Path, help="Папка run, де лежить matches.json")
    parser.add_argument("--source-folder", type=str, default="Статті", help="Папка з вихідними статтями")
    parser.add_argument("--output-folder", type=str, default="Статті_норм", help="Куди зберігати нормалізовані")
    parser.add_argument("--report", type=Path, default=None, help="Шлях до JSON звіту")
    parser.add_argument("--skip-header-block", action="store_true", help="Пропустити розбір шапки в кроці нормалізації")
    parser.add_argument("--debug-logs", action="store_true", help="Зберігати технічні per-file логи у Статті_норм/logs")
    args = parser.parse_args()

    run_dir = args.run_dir.resolve()
    source_folder = args.source_folder
    if source_folder == "Статті":
        source_folder = "Статті"
    source = run_dir / source_folder
    if not source.exists():
        alt = run_dir / "Статті"
        if alt.exists():
            source = alt
        else:
            raise SystemExit(f"Не знайдено папку статей: {source}")
    output_folder = args.output_folder
    if output_folder == "Статті_норм":
        output_folder = "Статті_норм"
    output = run_dir / output_folder
    report = args.report or (run_dir / "normalize_report.json")

    sys.argv = [
        sys.argv[0],
        str(source),
        "--output",
        str(output),
        "--report",
        str(report),
    ]
    if args.debug_logs:
        sys.argv.append("--debug-logs")
    stage_start = time.perf_counter()
    normalize_folder_main()
    stage_normalize = time.perf_counter() - stage_start
    print(f"[normalize] stage normalize_folder: {stage_normalize:.2f}s")
    stage_start = time.perf_counter()
    stats = _update_matches_cleaned_paths(run_dir, output)
    stage_update_matches = time.perf_counter() - stage_start
    print(f"[normalize] stage update_matches: {stage_update_matches:.2f}s")
    stage_start = time.perf_counter()
    order_stats = _enforce_primary_order(run_dir, output, write_logs=bool(args.debug_logs))
    stage_block_order = time.perf_counter() - stage_start
    print(f"[normalize] stage block_order: {stage_block_order:.2f}s")
    stage_start = time.perf_counter()
    title_stats = _apply_titles_to_normalized(run_dir, output, write_logs=bool(args.debug_logs))
    stage_title_align = time.perf_counter() - stage_start
    print(f"[normalize] stage title_align: {stage_title_align:.2f}s")
    stage_header_block = 0.0
    if not args.skip_header_block:
        stage_start = time.perf_counter()
        _apply_header_block(output, run_dir)
        stage_header_block = time.perf_counter() - stage_start
        print(f"[normalize] stage header_block: {stage_header_block:.2f}s")
    stage_start = time.perf_counter()
    update_dashboard_from_run(run_dir, update_relocated=False, update_cleaned=True)
    stage_update_dashboard = time.perf_counter() - stage_start
    print(f"[normalize] stage update_dashboard: {stage_update_dashboard:.2f}s")
    debug_log_path = _write_consolidated_log(
        run_dir,
        source_dir=source,
        output_dir=output,
        report_path=report,
        update_matches_stats=stats,
        title_stats=title_stats,
        order_stats=order_stats,
        stage_sec={
            "normalize_folder": round(stage_normalize, 3),
            "update_matches": round(stage_update_matches, 3),
            "block_order": round(stage_block_order, 3),
            "header_block": round(stage_header_block, 3),
            "title_align": round(stage_title_align, 3),
            "update_dashboard": round(stage_update_dashboard, 3),
        },
        debug_logs=bool(args.debug_logs),
    )
    print(f"[normalize] total: {time.perf_counter() - total_start:.2f}s")
    print(f"Готово. Нормалізовано у: {output}")
    print(f"Звіт: {report}")
    print(f"[normalize] debug JSON: {debug_log_path}")


if __name__ == "__main__":
    main()
