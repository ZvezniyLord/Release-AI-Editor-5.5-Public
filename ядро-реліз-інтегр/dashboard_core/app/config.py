from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ..constants import DEFAULT_SECTIONS_PATH, DEFAULT_TEMPLATE_PATH


@dataclass(slots=True)
class AppConfig:
    input_dir: Path
    authors_path: Path
    output_root: Path
    sections_path: Path = DEFAULT_SECTIONS_PATH
    template_path: Path = DEFAULT_TEMPLATE_PATH
    output_name: str = "zhurnal"
    threshold: float = 0.80
    preclean_sources: bool = False
    convert_mode: str = "auto"
    interactive_match: bool = False
    interactive_min_score: float = 0.10
    interactive_max_score: float = 0.80
    interactive_add_unknown: bool = False
    run_slug_override: str | None = None
    _run_slug: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.run_slug_override:
            self._run_slug = self.run_slug_override
            return
        safe_name = self.output_name.strip() or "zhurnal"
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._run_slug = f"{safe_name}_{stamp}"

    @property
    def run_slug(self) -> str:
        return self._run_slug

    @property
    def run_dir(self) -> Path:
        return self.output_root / self._run_slug

    @property
    def journal_path(self) -> Path:
        return self.run_dir / f"{self.output_name}.docx"

    @property
    def dashboard_path(self) -> Path:
        return self.run_dir / "dashboard_perevirky.xlsx"

    @property
    def summary_json_path(self) -> Path:
        return self.run_dir / "summary.json"

    @property
    def matches_json_path(self) -> Path:
        return self.run_dir / "matches.json"

    @property
    def diagnostics_json_path(self) -> Path:
        return self.run_dir / "diagnostics.json"

    @property
    def word_objects_json_path(self) -> Path:
        return self.run_dir / "word_objects_check.json"

    @property
    def sorted_articles_json_path(self) -> Path:
        return self.run_dir / "sorted_articles.json"

    @property
    def manifest_json_path(self) -> Path:
        return self.run_dir / "manifest.json"

    @property
    def technical_report_path(self) -> Path:
        return self.run_dir / "tekhnichnyi_zvit.md"

    def ensure_dirs(self) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
