from pathlib import Path


class DraftInputIntegrityError(RuntimeError):
    def __init__(self, missing_sources: list[Path]) -> None:
        self.missing_sources = missing_sources
        details = "\n".join(f"- {path}" for path in missing_sources)
        super().__init__(
            "Чернетку не створено: відсутні підготовлені файли статей:\n"
            f"{details}"
        )


def resolve_source_path(match: dict, source_folder: Path | None) -> Path:
    source_path = Path(
        match.get("cleaned_path")
        or match.get("relocated_path")
        or match.get("matched_path")
        or ""
    )
    if source_folder is not None and source_path.name:
        source_path = Path(source_folder) / source_path.name
    return source_path


def validate_source_files(
    ordered_sections: list[tuple[int, str, list[dict]]],
    source_folder: Path | None,
) -> None:
    missing_sources: list[Path] = []
    for _, _, entries in ordered_sections:
        for match in entries:
            source_path = resolve_source_path(match, source_folder)
            if not source_path.name or not source_path.exists():
                missing_sources.append(source_path)
    if missing_sources:
        raise DraftInputIntegrityError(missing_sources)
