from __future__ import annotations

from pathlib import Path


def _maybe_align_titles(
    draft_path: Path,
    threshold: float,
    auto: bool,
    *,
    run_dir: Path | None = None,
    titles_override: list[str] | None = None,
) -> dict | None:
    try:
        from core.align_titles_interactive import align_titles
    except Exception:
        return None
    run_dir = run_dir or draft_path.parent
    matches_path = run_dir / "matches.json"
    if not matches_path.exists():
        return None
    return align_titles(
        draft_path,
        run_dir,
        threshold=threshold,
        auto=auto,
        titles_override=titles_override,
    )
