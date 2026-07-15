from __future__ import annotations

from pathlib import Path
import time

from ..core.models import CandidateDocument, ScanIssue
from ..core.non_article_filter import is_non_article_filename, is_non_article_text
from .folder_walker import collect_word_files
from .word_converter import convert_doc_to_docx
from .word_reader import WordPageCounter, collect_first_page_text


def collect_candidate_documents(
    base_dir: Path,
    *,
    convert_mode: str = "auto",
    converted_dir: Path | None = None,
    log_callback=None,
    cancel_event=None,
) -> tuple[dict[Path, CandidateDocument], list[ScanIssue], dict[str, int]]:
    total_start = time.perf_counter()
    documents: dict[Path, CandidateDocument] = {}
    issues: list[ScanIssue] = []
    counts = {".doc": 0, ".docx": 0, "skipped": 0}

    all_paths = []
    if log_callback is not None:
        log_callback("[scan] Збір шляхів...")
    try:
        all_paths = collect_word_files(base_dir, cancel_event=cancel_event, log_callback=log_callback)
    finally:
        if log_callback is not None:
            log_callback(f"[scan] Зібрано шляхів: {len(all_paths)}")

    total_files = len(all_paths)
    with WordPageCounter() as page_counter:
        for idx, source_path in enumerate(all_paths, start=1):
            if cancel_event is not None and cancel_event.is_set():
                break
            if log_callback is not None:
                log_callback(f"[scan] {idx}/{total_files}: {source_path.name}")
            start_ts = time.perf_counter()
            if is_non_article_filename(source_path):
                issues.append(ScanIssue(path=str(source_path), reason="Відсіяно за назвою файлу"))
                counts["skipped"] += 1
                continue

            working_path = source_path
            converted = False
            if source_path.suffix.lower() in {".doc", ".dot", ".rtf", ".odt"}:
                if convert_mode == "skip":
                    issues.append(ScanIssue(path=str(source_path), reason="Пропущено не-docx формат (convert_mode=skip)"))
                    counts["skipped"] += 1
                    continue
                try:
                    conv_start = time.perf_counter()
                    working_path = convert_doc_to_docx(source_path, target_dir=converted_dir)
                    converted = True
                    conv_elapsed = time.perf_counter() - conv_start
                    if log_callback is not None and conv_elapsed >= 1.0:
                        log_callback(f"[scan] повільна конвертація {conv_elapsed:.2f}s: {source_path.name}")
                except Exception as error:
                    issues.append(ScanIssue(path=str(source_path), reason=f"Помилка конвертації Word: {error}"))
                    counts["skipped"] += 1
                    continue

            try:
                read_start = time.perf_counter()
                preview_text, chunks = collect_first_page_text(working_path)
                read_elapsed = time.perf_counter() - read_start
                if log_callback is not None and read_elapsed >= 1.0:
                    log_callback(f"[scan] повільне читання {read_elapsed:.2f}s: {working_path.name}")
            except Exception as error:
                issues.append(ScanIssue(path=str(source_path), reason=f"Помилка читання Word: {error}"))
                counts["skipped"] += 1
                continue

            if not preview_text:
                issues.append(ScanIssue(path=str(source_path), reason="Порожній або нечитабельний перший блок тексту"))
                counts["skipped"] += 1
                continue

            if is_non_article_text(preview_text):
                issues.append(ScanIssue(path=str(source_path), reason="Відсіяно за текстом першої сторінки"))
                counts["skipped"] += 1
                continue

            page_count = page_counter.count(working_path)
            if page_count is not None and page_count <= 1:
                issues.append(ScanIssue(
                    path=str(source_path),
                    reason=f"Відсіяно як ймовірну анкету: документ має {page_count} сторінку",
                ))
                counts["skipped"] += 1
                continue

            documents[source_path.resolve()] = CandidateDocument(
                source_path=source_path.resolve(),
                working_path=working_path.resolve(),
                relative_path=str(source_path.relative_to(base_dir)),
                text_preview=preview_text,
                text_chunks=chunks,
                converted_from_doc=converted,
                page_count=page_count,
            )
            counts[source_path.suffix.lower()] = counts.get(source_path.suffix.lower(), 0) + 1
            if log_callback and (len(documents) + counts["skipped"]) % 50 == 0:
                log_callback(f"[scan] kept={len(documents)} skipped={counts['skipped']}")
            if log_callback is not None:
                elapsed = time.perf_counter() - start_ts
                if elapsed >= 2.0:
                    log_callback(f"[scan] повільний файл {elapsed:.2f}s: {source_path.name}")

    elapsed_total = time.perf_counter() - total_start
    if log_callback is not None:
        log_callback(
            f"[scan] done: kept={len(documents)} skipped={counts['skipped']} total={len(all_paths)} in {elapsed_total:.2f}s"
        )
    return documents, issues, counts
