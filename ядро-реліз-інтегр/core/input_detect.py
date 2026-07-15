from __future__ import annotations

from pathlib import Path


PARTICIPANT_NAMES = {"учасники", "учасник", "Учасники", "Учасник"}
APPLICATION_NAMES = {"заявки", "заявка", "Заявки", "Заявка"}


def _name_match(path: Path, variants: set[str]) -> bool:
    return path.name.lower() in {v.lower() for v in variants}


def find_required_subdirs(target: Path) -> tuple[Path, Path]:
    participants = next((p for p in target.iterdir() if p.is_dir() and _name_match(p, PARTICIPANT_NAMES)), None)
    applications = next((p for p in target.iterdir() if p.is_dir() and _name_match(p, APPLICATION_NAMES)), None)
    if participants and applications:
        return participants, applications

    participant_candidates = [p for p in target.rglob("*") if p.is_dir() and _name_match(p, PARTICIPANT_NAMES)]
    for pc in participant_candidates:
        sibling = next((s for s in pc.parent.iterdir() if s.is_dir() and _name_match(s, APPLICATION_NAMES)), None)
        if sibling:
            return pc, sibling

    if participant_candidates:
        app_candidates = [p for p in target.rglob("*") if p.is_dir() and _name_match(p, APPLICATION_NAMES)]
        if app_candidates:
            return participant_candidates[0], app_candidates[0]

    raise FileNotFoundError("Не знайдено папки 'учасники' та 'заявки' (рекурсивний пошук)")


def pick_excel(participants_dir: Path) -> Path:
    excel_candidates = list(participants_dir.glob("*.xlsx")) + list(participants_dir.glob("*.xlsm"))
    if not excel_candidates:
        raise FileNotFoundError("У папці 'учасники' не знайдено Excel-файл")
    excel_candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return excel_candidates[0]
