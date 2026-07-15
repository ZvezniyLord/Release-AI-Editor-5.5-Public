from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def process_header_block(normalized_folder: Path, report_path: Path) -> None:
    module_root = Path(__file__).resolve().parents[2]
    shapka_script = module_root / "shapka_core" / "shapka_main.py"
    cmd = [
        str(Path(sys.executable)),
        str(shapka_script),
        str(normalized_folder),
        "--output-json",
        str(report_path),
    ]
    subprocess.run(cmd, check=False)
