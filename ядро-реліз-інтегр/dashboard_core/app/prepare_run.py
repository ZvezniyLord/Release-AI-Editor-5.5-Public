from __future__ import annotations

from pathlib import Path

from .config import AppConfig
from ..outputs.dashboard_writer import build_dashboard
from ..io.document_catalog import collect_candidate_documents
from ..io.excel_reader import load_articles_from_excel, match_section_label
from ..outputs.json_report_writer import write_json
from ..core.matcher import match_articles
from ..core.models import PrepareResult, ArticleRecord, MatchRecord, CandidateDocument
from ..core.sections_loader import load_sections
from ..core.interactive_prompts import ask_yes_no, ask_text
from ..outputs.workspace_state import write_last_run_pointer


def _interactive_add_unknown_documents(
    documents: list[CandidateDocument],
    sections: list[dict],
    matches: list[MatchRecord],
    articles: list[ArticleRecord],
    working_paths: dict[Path, Path],
    log_callback=None,
) -> int:
    added = 0
    for doc in documents:
        label = doc.relative_path or doc.source_path.name
        message = f"Документ без рядка в Excel:\n{label}\n\nДодати у дашборд?"
        if not ask_yes_no(message, title="Додати документ"):
            continue

        title = ask_text("Назва статті", default=doc.source_path.stem)
        if title is None or not title.strip():
            continue
        # Use a standard single-line prompt here; custom multiline Tk dialog can hang
        # on some Windows setups when called after a messagebox flow.
        authors_raw = ask_text("Автори (через кому)", default="", multiline=False) or ""
        authors = [a.strip() for a in authors_raw.split(",") if a.strip()]
        section_raw = ask_text("Секція (номер або назва)", default="") or ""
        section_number, section_ua, section_en = match_section_label(
            section_raw,
            sections,
            allow_plain_number=True,
        )

        article = ArticleRecord(
            title=title.strip(),
            authors=authors,
            section_ua=section_ua,
            section_en=section_en,
            section_number=section_number,
        )
        match = MatchRecord(
            title=article.title,
            authors=article.authors,
            section_ua=article.section_ua,
            section_en=article.section_en,
            section_number=article.section_number,
            match_method="interactive_added",
            matched_path=str(doc.source_path),
            score=1.0,
            working_path=str(doc.working_path),
            note="Додано вручну: відсутнє в Excel",
        )
        articles.append(article)
        matches.append(match)
        working_paths[doc.source_path] = doc.working_path
        added += 1
        if log_callback is not None:
            log_callback(f"[match] додано вручну: {doc.source_path.name}")
    return added


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
        converted_dir=config.run_dir / "_converted_docx",
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
        interactive=config.interactive_match,
        interactive_min_score=config.interactive_min_score,
        interactive_max_score=config.interactive_max_score,
    )
    write_progress("match", {"status": "done", "matches": len(matches), "missing": len(missing_articles)})

    unknown_added = 0
    if config.interactive_add_unknown:
        used_paths = set(working_paths.keys())
        unknown_docs = [doc for path, doc in documents.items() if path not in used_paths]
        if unknown_docs:
            sections = load_sections(config.sections_path)
            unknown_added = _interactive_add_unknown_documents(
                unknown_docs,
                sections,
                matches,
                articles,
                working_paths,
                log_callback=emit,
            )

    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeError("Prepare cancelled.")
    emit("4/4 Пишу JSON-звіти та дашборд...")

    diagnostics_payload = {
        "scan_issues": scan_issues,
        "raw_rows_count": len(raw_rows),
        "candidate_document_count": len(documents),
        "format_counts": format_counts,
        "missing_titles": [article.title for article in missing_articles],
        "unknown_documents_added": unknown_added,
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
        "interactive_match": config.interactive_match,
        "interactive_min_score": config.interactive_min_score,
        "interactive_max_score": config.interactive_max_score,
        "interactive_add_unknown": config.interactive_add_unknown,
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
