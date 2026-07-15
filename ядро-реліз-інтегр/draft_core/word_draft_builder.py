from __future__ import annotations

from collections import defaultdict
import json
import time
import shutil
import tempfile
from pathlib import Path

from .constants import WORD_SAVE_AS_DOCX
from .style_registry import load_style_registry, resolve_from_registry
from .draft_sections import _ensure_paragraph_style, _insert_heading
from .draft_insert import _insert_document, _center_media_in_range
from .draft_references import _restart_reference_numbering_in_range
from .draft_style_patch import _patch_tabletext_style, _debug_tables_in_range
from .draft_input import resolve_source_path, validate_source_files
import sys
from pathlib import Path as _Path
_SHARED_DIR = _Path(__file__).resolve().parents[2] / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from word_com import start_word_app, open_document_from_template, shutdown_word_app, WordComError
from pathlib import Path as _Path2

_DEBUG_DRAFT_LOG = _Path2(__file__).resolve().parents[1] / "draft_table_debug.json"
_DEBUG_TABLES_LOG = _Path2(__file__).resolve().parents[1] / "draft_tables_debug.json"


def build_draft_with_word(
    template_path: Path,
    output_path: Path,
    matches: list[dict],
    *,
    source_folder: Path | None = None,
    log_callback=None,
    word_app=None,
) -> None:
    grouped: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for match in matches:
        if match.get("match_method") in {"missing", "missing_source_file", "free_listener"}:
            continue
        section_number = match.get("section_number") if match.get("section_number") is not None else 9999
        section_name = match.get("section_en") or match.get("section_ua") or "No section"
        grouped[(section_number, section_name)].append(match)

    ordered_sections = sorted(
        ((section_number, section_name, entries) for (section_number, section_name), entries in grouped.items()),
        key=lambda item: (item[0], item[1].casefold()),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    template_path = Path(template_path).resolve()
    output_path = Path(output_path).resolve()
    if log_callback is not None:
        log_callback(f"[draft] шаблон: {template_path}")
        log_callback(f"[draft] вихід: {output_path}")
    if not template_path.exists():
        raise FileNotFoundError(f"Шаблон не знайдено: {template_path}")
    validate_source_files(ordered_sections, source_folder)

    # Якщо шлях містить не-ASCII, копіюємо шаблон у temp для надійності COM
    safe_template = template_path
    try:
        template_path.as_posix().encode("ascii")
    except UnicodeEncodeError:
        temp_dir = Path(tempfile.gettempdir()) / "draft_core_templates"
        temp_dir.mkdir(parents=True, exist_ok=True)
        safe_template = temp_dir / "template.dotx"
        shutil.copy2(template_path, safe_template)
        if log_callback is not None:
            log_callback(f"[draft] використовую temp-шаблон: {safe_template}")

    word = None
    document = None
    inserted_log: list[dict[str, object]] = []
    missing_sources: list[str] = []
    skipped_methods: list[str] = []
    try:
        if word_app is not None:
            word = word_app
        else:
            word = start_word_app(log_callback=log_callback)
        last_error = None
        for attempt in range(1, 3):
            try:
                document = open_document_from_template(word, str(safe_template))
                break
            except Exception as error:
                last_error = error
                if log_callback is not None:
                    log_callback(f"[wordcom] не вдалося відкрити шаблон, повтор {attempt}/2...")
                time.sleep(1.5)
        if document is None and last_error is not None:
            raise last_error

        registry = load_style_registry()
        section_style = resolve_from_registry(document, registry, "section")
        if not section_style:
            section_style = _ensure_paragraph_style(
                document,
                "SECTION",
                ["Heading 1", "Заголовок 1", "Section", "СЕКЦІЯ заголовок", "Normal"],
            )

        # Debug: capture default table style and document default
        try:
            debug_info = {
                "default_table_style": str(getattr(document, "DefaultTableStyle", "")),
                "normal_style": str(getattr(document.Styles, "DefaultParagraphFont", "")),
            }
            _DEBUG_DRAFT_LOG.write_text(json.dumps(debug_info, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

        total_inserted = sum(len(entries) for _, _, entries in ordered_sections)
        inserted_counter = 0
        for _, section_name, section_matches in ordered_sections:
            if log_callback is not None:
                log_callback(f"[draft] секція: {section_name} (статей: {len(section_matches)})")
            _insert_heading(document, section_name, section_style)
            for match in section_matches:
                inserted_counter += 1
                method = str(match.get("match_method") or "")
                if method in {"missing", "missing_source_file", "free_listener"}:
                    skipped_methods.append(method)
                    continue
                source_path = resolve_source_path(match, source_folder)
                if not source_path.exists():
                    missing_sources.append(str(source_path))
                    if log_callback is not None:
                        log_callback(f"[draft] файл не знайдено: {source_path}")
                    continue
                if log_callback is not None:
                    log_callback(f"[draft] {inserted_counter}/{total_inserted} {source_path.name}")
                try:
                    insert_range = _insert_document(
                        document,
                        source_path,
                        add_page_break=inserted_counter < total_inserted,
                    )
                    if insert_range:
                        _center_media_in_range(document, insert_range[0], insert_range[1])
                        _restart_reference_numbering_in_range(
                            document,
                            insert_range[0],
                            insert_range[1],
                        )
                        _debug_tables_in_range(
                            document,
                            insert_range[0],
                            insert_range[1],
                            _DEBUG_TABLES_LOG,
                            source_name=source_path.name,
                        )
                        inserted_log.append(
                            {
                                "source": source_path.name,
                                "source_path": str(source_path),
                                "section": section_name,
                            }
                        )
                except Exception as error:
                    if log_callback is not None:
                        log_callback(f"[draft] помилка вставки: {source_path.name}: {error}")
                    continue

        document.SaveAs2(str(output_path), FileFormat=WORD_SAVE_AS_DOCX)
        _patch_tabletext_style(output_path)
    except WordComError as error:
        raise RuntimeError(
            "Не вдалося запустити Word COM або відкрити шаблон. Закрий усі вікна Word і спробуй знову."
        ) from error
    finally:
        if document is not None:
            document.Close(False)
        # Закриваємо Word лише якщо ми його запускали тут.
        if word_app is None:
            shutdown_word_app(word)
        if output_path.exists():
            _patch_tabletext_style(output_path)
        # Write draft insertion report
        try:
            report = {
                "inserted_count": len(inserted_log),
                "inserted": inserted_log,
                "missing_sources": missing_sources,
                "skipped_methods": skipped_methods,
            }
            report_path = output_path.with_suffix(".insert_report.json")
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
