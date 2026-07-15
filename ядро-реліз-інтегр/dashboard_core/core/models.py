from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ArticleRecord:
    title: str
    authors: list[str]
    section_ua: str
    section_en: str
    section_number: int | None
    registration_numbers: list[str] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)
    is_free_listener: bool = False


@dataclass(slots=True)
class CandidateDocument:
    source_path: Path
    working_path: Path
    relative_path: str
    text_preview: str
    text_chunks: list[str]
    converted_from_doc: bool = False
    page_count: int | None = None
    skip_reason: str = ""


@dataclass(slots=True)
class MatchRecord:
    title: str
    authors: list[str]
    section_ua: str
    section_en: str
    section_number: int | None
    match_method: str
    matched_path: str
    score: float
    working_path: str = ""
    note: str = ""
    relocated_path: str = ""
    cleaned_path: str = ""
    cleaned_assets: dict | None = None


@dataclass(slots=True)
class ScanIssue:
    path: str
    reason: str


@dataclass(slots=True)
class ObjectCheckRecord:
    path: str
    inline_shapes: int
    floating_shapes: int
    tables: int
    ole_objects: int
    charts: int
    media_files: int
    embedding_files: int
    media_names: list[str] = field(default_factory=list)
    embedding_names: list[str] = field(default_factory=list)
    warning: str = ""


@dataclass(slots=True)
class PipelineResult:
    run_dir: Path
    journal_path: Path
    dashboard_path: Path
    manifest_json_path: Path
    summary_json_path: Path
    matches_json_path: Path
    diagnostics_json_path: Path
    technical_report_path: Path
    articles_total: int
    articles_matched: int
    articles_missing: int


@dataclass(slots=True)
class PrepareResult:
    run_dir: Path
    journal_path: Path
    dashboard_path: Path
    manifest_json_path: Path
    summary_json_path: Path
    matches_json_path: Path
    diagnostics_json_path: Path
    sorted_articles_json_path: Path
    word_objects_json_path: Path
    technical_report_path: Path
    articles: list[ArticleRecord]
    matches: list[MatchRecord]
    working_paths: dict[Path, Path]
    raw_rows: list[dict[str, Any]]
    scan_issues: list[ScanIssue]
    format_counts: dict[str, int]
    missing_articles: list[ArticleRecord]
