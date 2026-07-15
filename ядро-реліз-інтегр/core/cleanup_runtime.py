from __future__ import annotations

from pathlib import Path
import subprocess


def _kill_word() -> None:
    try:
        subprocess.run(["taskkill", "/F", "/IM", "WINWORD.EXE"], check=False, capture_output=True)
    except Exception:
        pass


def _cleanup_lock_files(root: Path) -> None:
    try:
        for lock in root.rglob("~$*.docx"):
            try:
                lock.unlink()
            except Exception:
                continue
    except Exception:
        pass


def pre_run_cleanup(root: Path | None = None) -> None:
    _kill_word()
    if root is not None:
        _cleanup_lock_files(root)


def post_run_cleanup(root: Path | None = None) -> None:
    _kill_word()
    if root is not None:
        _cleanup_lock_files(root)


def main() -> None:
    import sys
    root = None
    if len(sys.argv) > 1:
        root = Path(sys.argv[1])
    pre_run_cleanup(root)
    post_run_cleanup(root)


if __name__ == "__main__":
    main()
