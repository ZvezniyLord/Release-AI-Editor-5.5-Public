from __future__ import annotations

import argparse
import json
import sys
import re
from pathlib import Path
from difflib import SequenceMatcher

from docx import Document
import tkinter as tk
from tkinter import messagebox


def _normalize(text: str) -> str:
    text = (text or "").strip().casefold()
    text = re.sub(r"[^a-zа-яієї0-9]+", " ", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_compact(text: str) -> str:
    text = (text or "").strip().casefold()
    return re.sub(r"[^a-zа-яієї0-9]+", "", text, flags=re.IGNORECASE)


def _load_matches(run_dir: Path) -> list[dict]:
    matches_path = run_dir / "matches.json"
    if not matches_path.exists():
        raise FileNotFoundError(f"Не знайдено {matches_path}")
    data = json.loads(matches_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("matches.json має бути списком")
    return data


def _collect_paragraphs(draft_path: Path) -> list[str]:
    doc = Document(draft_path)
    paras: list[str] = []
    for p in doc.paragraphs:
        text = (p.text or "").strip()
        if not text:
            continue
        # ignore extremely long paragraphs (likely body text)
        if len(text) > 260:
            continue
        paras.append(text)
    return paras


def _find_best_candidate(title: str, paragraphs: list[str], threshold: float) -> tuple[str | None, float]:
    target = _normalize_compact(title)
    if not target:
        return None, 0.0
    best_text = None
    best_score = 0.0
    for text in paragraphs:
        comp = _normalize_compact(text)
        if not comp:
            continue
        score = SequenceMatcher(None, target, comp).ratio()
        if score > best_score:
            best_score = score
            best_text = text
    if best_score >= threshold:
        return best_text, best_score
    return None, best_score


def _ask_user(title: str, candidate: str, score: float) -> bool:
    message = f"JSON:\n{title}\n\nDOC:\n{candidate}\n\nscore: {score:.3f}\n\nПрийняти?"
    # If no TTY, fall back to GUI prompt.
    try:
        if sys.stdin is not None and sys.stdin.isatty():
            answer = input(f"{message}\n(y/n): ").strip().lower()
            return answer in {"y", "yes", "т", "так"}
    except Exception:
        pass

    root = tk.Tk()
    root.withdraw()
    try:
        return messagebox.askyesno("Вирівнювання назв", message)
    finally:
        root.destroy()


def align_titles(
    draft_path: Path,
    run_dir: Path,
    *,
    threshold: float,
    auto: bool,
    titles_override: list[str] | None = None,
) -> dict:
    matches = _load_matches(run_dir)
    paragraphs = _collect_paragraphs(draft_path)

    if titles_override is not None:
        # Використовуємо лише конкретні назви, коли працюємо з окремою статтею.
        titles = [t for t in titles_override if t and str(t).strip()]
    else:
        titles = []
        for item in matches:
            if not isinstance(item, dict):
                continue
            if (item.get("match_method") or "").strip() != "title_match":
                continue
            title = (item.get("title") or "").strip()
            if title:
                titles.append(title)

    title_hits = set()
    para_norm = {_normalize_compact(p): p for p in paragraphs}
    for title in titles:
        if _normalize_compact(title) in para_norm:
            title_hits.add(title)

    missing = [t for t in titles if t not in title_hits]
    changes = []
    skipped = []
    if missing:
        for title in missing:
            best_text, score = _find_best_candidate(title, paragraphs, threshold)
            if not best_text:
                skipped.append({"title": title, "reason": "no_candidate", "score": score})
                continue

            if auto:
                accept = True
            else:
                accept = _ask_user(title, best_text, score)

            if not accept:
                skipped.append({"title": title, "candidate": best_text, "score": score, "reason": "rejected"})
                continue

            for item in matches:
                if not isinstance(item, dict):
                    continue
                if (item.get("title") or "").strip() == title:
                    item["title"] = best_text
                    changes.append({"from": title, "to": best_text, "score": score})
                    break

    if changes:
        matches_path = run_dir / "matches.json"
        matches_path.write_text(json.dumps(matches, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "draft": str(draft_path),
        "run_dir": str(run_dir),
        "threshold": threshold,
        "titles_override": titles_override,
        "changes": changes,
        "skipped": skipped,
    }
    report_path = draft_path.parent / "align_titles_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Вирівнює назви у matches.json з фактичними заголовками у чернетці (з підтвердженням)."
    )
    parser.add_argument("draft", type=Path, help="Шлях до draft_journal.docx")
    parser.add_argument("run_dir", type=Path, help="Папка run, де лежить matches.json")
    parser.add_argument("--threshold", type=float, default=0.9, help="Поріг схожості (0..1)")
    parser.add_argument("--auto", action="store_true", help="Автоматично приймати всі збіги вище порога")
    args = parser.parse_args()

    draft_path = args.draft.resolve()
    run_dir = args.run_dir.resolve()
    report = align_titles(draft_path, run_dir, threshold=args.threshold, auto=args.auto)
    print(f"Оновлено: {len(report['changes'])}. Звіт: {draft_path.parent / 'align_titles_report.json'}")


if __name__ == "__main__":
    main()
