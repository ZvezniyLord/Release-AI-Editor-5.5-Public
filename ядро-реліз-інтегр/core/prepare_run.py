from __future__ import annotations

from pathlib import Path

from .config import AppConfig
from ..outputs.dashboard_writer import build_dashboard
from ..io.document_catalog import collect_candidate_documents
from ..io.excel_reader import load_articles_from_excel
from ..outputs.json_report_writer import write_json
from ..core.matcher import match_articles
from ..core.models import PrepareResult
from ..outputs.workspace_state import write_last_run_pointer


def prepare_run(config: AppConfig, log_callback=None, cancel_event=None) -> PrepareResult:
    def emit(message: str) -> None:
        if log_callback is not None:
            log_callback(message)

    def write_progress(stage: str, payload: dict) -> None:
        progress_path = config.run_dir / "prepare_progress.json"
        write_json(progress_path, {"stage": stage, **payload})

    config.ensure_dirs()

    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeError("Prepare cancelled.")
    emit("1/4 Читаю Excel учасників...")
    write_progress("excel", {"status": "start"})
    articles, raw_rows = load_articles_from_excel(config.authors_path, config.sections_path)
    write_progress("excel", {"status": "done", "articles": len(articles), "rows": len(raw_rows)})

    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeError("Prepare cancelled.")
    emit("2/4 Сканую папку заявок...")
    write_progress("scan", {"status": "start"})
    documents, scan_issues, format_counts = collect_candidate_documents(
        config.input_dir,
        convert_mode=config.convert_mode,
        log_callback=emit,
        cancel_event=cancel_event,
    )
    write_progress("scan", {"status": "done", "documents": len(documents), "skipped": len(scan_issues)})

    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeError("Prepare cancelled.")
    emit("3/4 Зіставляю статті з файлами...")
    write_progress("match", {"status": "start"})
    matches, missing_articles, working_paths = match_articles(
        articles,
        documents,
        config.threshold,
        base_dir=config.input_dir,
        log_callback=emit,
    )
    write_progress("match", {"status": "done", "matches": len(matches), "missing": len(missing_articles)})

    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeError("Prepare cancelled.")
    emit("4/4 Пишу JSON-звіти та дашборд...")

    diagnostics_payload = {
        "scan_issues": scan_issues,
        "raw_rows_count": len(raw_rows),
        "candidate_document_count": len(documents),
        "format_counts": format_counts,
        "missing_titles": [article.title for article in missing_articles],
    }
    summary_payload = {
        "articles_total": len([item for item in articles if not item.is_free_listener]),
        "articles_matched": len(
            [item for item in matches if item.match_method not in {"missing", "missing_source_file", "free_listener"}]
        ),
        "articles_missing": len(missing_articles),
        "free_listeners": len([item for item in articles if item.is_free_listener]),
        "journal_path": config.journal_path,
        "dashboard_path": config.dashboard_path,
        "threshold": config.threshold,
        "format_counts": format_counts,
    }
    manifest_payload = {
        "pipeline_name": "Dashboard Core",
        "pipeline_version": "0.1.0",
        "run_dir": config.run_dir,
        "input_dir": config.input_dir,
        "authors_path": config.authors_path,
        "sections_path": config.sections_path,
        "template_path": config.template_path,
        "journal_path": config.journal_path,
        "dashboard_path": config.dashboard_path,
        "summary_json_path": config.summary_json_path,
        "matches_json_path": config.matches_json_path,
        "sorted_articles_json_path": config.sorted_articles_json_path,
        "diagnostics_json_path": config.diagnostics_json_path,
        "word_objects_json_path": config.word_objects_json_path,
        "technical_report_path": config.technical_report_path,
        "output_name": config.output_name,
        "threshold": config.threshold,
    }

    write_json(config.sorted_articles_json_path, articles)
    write_json(config.matches_json_path, matches)
    write_json(config.diagnostics_json_path, diagnostics_payload)
    write_json(config.summary_json_path, summary_payload)
    write_json(config.manifest_json_path, manifest_payload)

    build_dashboard(config.dashboard_path, articles, matches)
    write_progress("dashboard", {"status": "done", "path": str(config.dashboard_path)})
    write_last_run_pointer(
        run_dir=config.run_dir,
        manifest_path=config.manifest_json_path,
        journal_path=config.journal_path,
        summary_path=config.summary_json_path,
    )

    return PrepareResult(
        run_dir=config.run_dir,
        journal_path=config.journal_path,
        dashboard_path=config.dashboard_path,
        manifest_json_path=config.manifest_json_path,
        summary_json_path=config.summary_json_path,
        matches_json_path=config.matches_json_path,
        diagnostics_json_path=config.diagnostics_json_path,
        sorted_articles_json_path=config.sorted_articles_json_path,
        word_objects_json_path=config.word_objects_json_path,
        technical_report_path=config.technical_report_path,
        articles=articles,
        matches=matches,
        working_paths=working_paths,
        raw_rows=raw_rows,
        scan_issues=scan_issues,
        format_counts=format_counts,
        missing_articles=missing_articles,
    )
