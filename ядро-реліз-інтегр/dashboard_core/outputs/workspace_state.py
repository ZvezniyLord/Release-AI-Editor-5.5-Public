from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .json_report_writer import write_json


WORKSPACE_DIR = Path(__file__).resolve().parents[1] / "workspace"
LAST_RUN_PATH = WORKSPACE_DIR / "last_run.json"


def write_last_run_pointer(
    run_dir: Path,
    manifest_path: Path,
    journal_path: Path,
    summary_path: Path,
) -> None:
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    write_json(LAST_RUN_PATH, {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "run_dir": run_dir,
        "manifest_json_path": manifest_path,
        "journal_path": journal_path,
        "summary_json_path": summary_path,
    })
