from __future__ import annotations

import shutil
from pathlib import Path

from dashboard_core import AppConfig, prepare_run
from core.add_dashboard_stats import add_stats_sheet
from core.input_detect import find_required_subdirs, pick_excel
from core.excel_validate import validate_excel_headers
from shared.run_logger import make_logger
from shared.word_com import warmup_word
from shared.template_resolver import resolve_template_path
from shared.safe_shutdown import safe_shutdown


def run_dashboard(args) -> None:
    if args.target is None:
        raw = input("Вкажи шлях до цільової папки (учасники/заявки): ").strip().strip('"')
        if not raw:
            raise SystemExit("Порожній шлях.")
        target = Path(raw).resolve()
    else:
        target = args.target.resolve()
    participants_dir, applications_dir = find_required_subdirs(target)

    excel_path = pick_excel(participants_dir)
    validate_excel_headers(excel_path)

    run_root = args.output.resolve()
    run_root.mkdir(parents=True, exist_ok=True)

    copied_excel = run_root / excel_path.name
    shutil.copy2(excel_path, copied_excel)

    convert_mode = "auto"
    if getattr(args, "convert_mode", "auto") != "auto":
        print("[prep] convert_mode примусово встановлено в auto")
    config = AppConfig(
        input_dir=applications_dir,
        authors_path=copied_excel,
        output_root=run_root,
        output_name=args.name,
        threshold=args.threshold,
        preclean_sources=args.preclean,
        convert_mode=convert_mode,
        interactive_match=args.interactive_match,
        interactive_min_score=args.interactive_min_score,
        interactive_max_score=args.interactive_max_score,
        interactive_add_unknown=args.interactive_add_unknown,
    )

    logger = make_logger(run_root / "logs", name=f"dashboard_{args.name}")
    logger.info("start", target=str(target), participants=str(participants_dir), applications=str(applications_dir))

    print("[1/4] Читаю Excel та секції...")
    result = prepare_run(
        config,
        log_callback=lambda msg: (print(f"[prep] {msg}"), logger.log("prep", message=msg))[0],
    )

    print("[done] Створено:")
    print(f"- dashboard: {result.dashboard_path}")
    print(f"- summary:   {result.summary_json_path}")
    print(f"- matches:   {result.matches_json_path}")
    print(f"- manifest:  {result.manifest_json_path}")
    print(f"- diagnostics:{result.diagnostics_json_path}")
    print(f"- sorted:    {result.sorted_articles_json_path}")

    logger.info(
        "done",
        dashboard=str(result.dashboard_path),
        summary=str(result.summary_json_path),
        matches=str(result.matches_json_path),
        manifest=str(result.manifest_json_path),
        diagnostics=str(result.diagnostics_json_path),
        sorted=str(result.sorted_articles_json_path),
    )

    try:
        if args.no_stats:
            return
        warmup_word(template_path=str(resolve_template_path() or ""), log_callback=print, keep_open=True)
        if args.stats:
            add_stats_sheet(result.dashboard_path, dashboard_sheet_name=None, stats_sheet_name="Статистика")
            print("Вкладку 'Статистика' додано.")
            logger.info("stats_sheet", dashboard=str(result.dashboard_path))
            return
        answer = input("Створити вкладку статистики? (y/n): ").strip().lower()
        if answer in {"y", "yes", "так", "t"}:
            add_stats_sheet(result.dashboard_path, dashboard_sheet_name=None, stats_sheet_name="Статистика")
            print("Вкладку 'Статистика' додано.")
            logger.info("stats_sheet", dashboard=str(result.dashboard_path))
    finally:
        safe_shutdown(log_callback=print)
