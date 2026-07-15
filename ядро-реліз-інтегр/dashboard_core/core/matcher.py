from __future__ import annotations

from pathlib import Path
import re

from .models import ArticleRecord, CandidateDocument, MatchRecord
from .interactive_prompts import ask_yes_no
from .text_utils import canonical, similarity, translit_uk


ARTICLE_EVIDENCE_MARKERS = tuple(canonical(item) for item in (
    "УДК",
    "UDC",
    "Анотація",
    "Annotation",
    "Abstract",
    "Ключові слова",
    "Keywords",
    "Key words",
))

SERVICE_FORM_MARKERS = tuple(canonical(item) for item in (
    "Стовпець анкетної форми",
    "Інформація для заповнення",
    "Ім’я і прізвище автора публікації",
    "Назва статті",
))


def _document_article_priority(document: CandidateDocument) -> int:
    text_key = canonical(document.text_preview)
    score = sum(1 for marker in ARTICLE_EVIDENCE_MARKERS if marker and marker in text_key)
    if any(marker and marker in text_key for marker in SERVICE_FORM_MARKERS):
        score -= 2
    return score


def _soft_key(value: str) -> str:
    normalized = canonical(value)
    normalized = normalized.replace("zgh", "z").replace("zh", "z")
    normalized = normalized.replace("gh", "g").replace("kh", "k")
    normalized = normalized.replace("ye", "e").replace("ie", "e")
    normalized = normalized.replace("yi", "i").replace("iy", "i")
    normalized = normalized.replace("ya", "a").replace("ia", "a")
    normalized = re.sub(r"[^a-zа-яіїєґ]", "", normalized)
    return normalized


def _surname_variants(author: str) -> set[str]:
    parts = [part for part in str(author).split() if part]
    if not parts:
        return set()

    base = parts[-1]
    variants = {
        canonical(base),
        translit_uk(base),
    }
    expanded: set[str] = set()
    for value in variants:
        if not value:
            continue
        expanded.add(value)
        expanded.add(value.replace("yi", "y"))
        expanded.add(value.replace("yi", "i"))
        expanded.add(value.replace("yy", "y"))
        expanded.add(value.replace("iy", "i"))
        expanded.add(value.replace("ij", "i"))
        expanded.add(value.replace("skyi", "skiy"))
        expanded.add(value.replace("skyy", "skiy"))
        expanded.add(value.replace("skiy", "ski"))
        expanded.add(value.replace("zgh", "zh"))
        expanded.add(value.replace("gh", "g"))
        expanded.add(value.replace("kh", "h"))
        expanded.add(value.replace("h", "g"))
        expanded.add(value.replace("ye", "ie"))
        expanded.add(value.replace("ie", "ye"))
        expanded.add(value.replace("ye", "e"))
        expanded.add(value.replace("ia", "ya"))
        expanded.add(value.replace("ya", "ia"))
        expanded.add(value.replace("zh", "z"))
    return {item for item in expanded if item}


def _matching_author_folders(article: ArticleRecord, base_dir: Path) -> list[Path]:
    surname_keys: set[str] = set()
    for author in article.authors:
        surname_keys.update(_surname_variants(author))
    if not surname_keys:
        return []

    folders: list[Path] = []
    soft_keys = {_soft_key(key) for key in surname_keys if key}
    for path in base_dir.iterdir():
        if not path.is_dir():
            continue
        folder_tokens = " ".join({
            canonical(path.name),
            translit_uk(path.name),
            translit_uk(path.name).replace("h", "g"),
            translit_uk(path.name).replace("ye", "ie"),
            translit_uk(path.name).replace("gh", "g"),
        })
        folder_soft = _soft_key(folder_tokens)
        if any(key and key in folder_tokens for key in surname_keys) or any(key and key in folder_soft for key in soft_keys):
            folders.append(path)
    return folders


def _is_missing_source_file(
    article: ArticleRecord,
    documents: dict[Path, CandidateDocument],
    base_dir: Path | None,
) -> bool:
    if base_dir is None or not base_dir.exists():
        return False

    folders = _matching_author_folders(article, base_dir)
    if len(folders) != 1:
        return False

    folder = folders[0].resolve()
    if any(path.parent == folder for path in documents):
        return False

    try:
        return any(path.is_file() for path in folder.iterdir())
    except OSError:
        return False


def rank_candidates(title: str, documents: dict[Path, CandidateDocument]) -> list[tuple[Path, float, str]]:
    title_key = canonical(title)
    ranked: list[tuple[Path, float, str]] = []
    for path, document in documents.items():
        preview_key = canonical(document.text_preview)
        if title_key and title_key in preview_key:
            ranked.append((path, 1.0, "Збіг назви в першій сторінці"))
            continue

        best_score = 0.0
        reason = "Нечіткий збіг за фрагментами"
        for chunk in document.text_chunks:
            chunk_key = canonical(chunk)
            if not chunk_key:
                continue
            if title_key == chunk_key or title_key in chunk_key:
                best_score = 1.0
                reason = "Точний збіг заголовка у фрагменті"
                break
            score = similarity(title, chunk)
            if score > best_score:
                best_score = score
        ranked.append((path, best_score, reason))
    ranked.sort(key=lambda item: (item[1], _document_article_priority(documents[item[0]])), reverse=True)
    return ranked


def _normalize_score(value: float) -> float:
    if value > 1.0:
        return value / 100.0
    return value


def _ask_interactive_confirm(
    article: ArticleRecord,
    candidate_path: Path,
    score: float,
    reason: str,
    documents: dict[Path, CandidateDocument],
) -> bool:
    doc = documents.get(candidate_path)
    candidate_label = doc.relative_path if doc and doc.relative_path else candidate_path.name
    candidate_text = ""
    if doc is not None:
        candidate_text = (doc.text_preview or "").strip()
    if len(candidate_text) > 500:
        candidate_text = candidate_text[:500].rstrip() + "..."
    author_label = ", ".join(article.authors) if article.authors else "-"
    message = (
        "Кандидат для статті:\n"
        f"Назва з дашборду: {article.title}\n\n"
        f"Автори: {author_label}\n"
        f"Файл: {candidate_label}\n"
        f"score: {score:.2f}\n"
        f"Причина: {reason}\n\n"
        f"Текст кандидата:\n{candidate_text or '-'}\n\n"
        "Прийняти?"
    )
    return ask_yes_no(message, title="Підтвердження кандидата")
    author_label = ", ".join(article.authors) if article.authors else "-"
    message = (
        "Кандидат для статті:\n"
        f"{article.title}\n\n"
        f"Автори: {author_label}\n"
        f"Файл: {candidate_label}\n"
        f"score: {score:.2f}\n"
        f"Причина: {reason}\n\n"
        "Прийняти?"
    )
    return ask_yes_no(message, title="Підтвердження кандидата")


def _folder_fallback(article: ArticleRecord, documents: dict[Path, CandidateDocument], used_paths: set[Path]) -> tuple[Path | None, str]:
    surname_keys: set[str] = set()
    for author in article.authors:
        surname_keys.update(_surname_variants(author))
    if not surname_keys:
        return None, "Немає прізвища для fallback"

    candidates: dict[Path, list[Path]] = {}
    for path in documents:
        if path in used_paths:
            continue
        folder_name = path.parent.name
        file_name = path.stem
        folder_tokens = " ".join({
            canonical(folder_name),
            translit_uk(folder_name),
            translit_uk(folder_name).replace("h", "g"),
            canonical(file_name),
            translit_uk(file_name),
        })
        if any(key and key in folder_tokens for key in surname_keys):
            candidates.setdefault(path.parent, []).append(path)

    if len(candidates) != 1:
        return None, "Fallback за папкою не дав однозначного результату"
    folder_files = next(iter(candidates.values()))
    if len(folder_files) != 1:
        return None, "У папці автора кілька документів-кандидатів"
    return folder_files[0], "Fallback за назвою папки автора"


def match_articles(
    articles: list[ArticleRecord],
    documents: dict[Path, CandidateDocument],
    threshold: float,
    base_dir: Path | None = None,
    log_callback=None,
    *,
    interactive: bool = False,
    interactive_min_score: float = 0.10,
    interactive_max_score: float = 0.80,
) -> tuple[list[MatchRecord], list[ArticleRecord], dict[Path, Path]]:
    matches: list[MatchRecord] = []
    missing_articles: list[ArticleRecord] = []
    working_paths: dict[Path, Path] = {}
    used_paths: set[Path] = set()

    total = len(articles)
    min_score = _normalize_score(interactive_min_score)
    max_score = _normalize_score(interactive_max_score)
    if max_score < min_score:
        min_score, max_score = max_score, min_score

    for idx, article in enumerate(articles, start=1):
        if log_callback is not None:
            log_callback(f"[match] {idx}/{total} {article.title}")
        if article.is_free_listener:
            matches.append(MatchRecord(
                title=article.title,
                authors=article.authors,
                section_ua=article.section_ua,
                section_en=article.section_en,
                section_number=article.section_number,
                match_method="free_listener",
                matched_path="",
                score=1.0,
                working_path="",
                note="Вільний слухач не вставляється до журналу",
            ))
            continue

        ranked = rank_candidates(article.title, documents)
        chosen_path: Path | None = None
        chosen_score = 0.0
        chosen_note = ""
        chosen_method = ""

        if ranked:
            top_path, top_score, top_note = ranked[0]
            interactive_rejected = False
            if interactive and top_path not in used_paths and min_score <= top_score <= max_score:
                if log_callback is not None:
                    log_callback(f"[match] interactive {top_score:.2f}: {article.title} -> {top_path.name}")
                if _ask_interactive_confirm(article, top_path, top_score, top_note, documents):
                    chosen_path = top_path
                    chosen_score = top_score
                    chosen_note = f"Interactive підтверджено: {top_note}"
                    chosen_method = "interactive_confirm"
                else:
                    interactive_rejected = True
            if chosen_path is None and not interactive_rejected and top_path not in used_paths and top_score >= threshold:
                chosen_path = top_path
                chosen_score = top_score
                chosen_note = top_note
                chosen_method = "title_match"

        if chosen_path is None:
            fallback_path, fallback_note = _folder_fallback(article, documents, used_paths)
            if fallback_path is not None:
                chosen_path = fallback_path
                chosen_score = 0.0
                chosen_note = fallback_note
                chosen_method = "folder_fallback"

        if chosen_path is None:
            missing_articles.append(article)
            nearest = ranked[0] if ranked else None
            note = "Не знайдено відповідний документ"
            method = "missing"
            if _is_missing_source_file(article, documents, base_dir):
                note = "У папці автора є файли, але стаття як Word-документ відсутня або відсіяна"
                method = "missing_source_file"
            elif nearest is not None:
                note = f"Найкращий кандидат: {nearest[0].name} ({nearest[1]:.2f})"
            matches.append(MatchRecord(
                title=article.title,
                authors=article.authors,
                section_ua=article.section_ua,
                section_en=article.section_en,
                section_number=article.section_number,
                match_method=method,
                matched_path="",
                score=0.0,
                working_path="",
                note=note,
            ))
            continue

        used_paths.add(chosen_path)
        working_paths[chosen_path] = documents[chosen_path].working_path
        matches.append(MatchRecord(
            title=article.title,
            authors=article.authors,
            section_ua=article.section_ua,
            section_en=article.section_en,
            section_number=article.section_number,
            match_method=chosen_method,
            matched_path=str(chosen_path),
            score=chosen_score,
            working_path=str(documents[chosen_path].working_path),
            note=chosen_note,
        ))

    return matches, missing_articles, working_paths
