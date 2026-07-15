from __future__ import annotations

import atexit
import os
import tempfile
import time
from pathlib import Path

import sys
from pathlib import Path as _Path

from ..constants import WORD_SAVE_AS_DOCX

_SHARED_DIR = _Path(__file__).resolve().parents[2] / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from word_com import WordComError, open_document, shutdown_word_app, start_word_app

_TEMP_FILES: list[Path] = []
_CONVERT_CACHE: dict[str, tuple[int, int, Path]] = {}
_WORD_APP = None
_WORD_REUSE = os.getenv("WORD_COM_REUSE", "1").strip().lower() in {"1", "true", "yes", "y"}
_WORD_VERBOSE = os.getenv("WORD_COM_VERBOSE", "").strip().lower() in {"1", "true", "yes", "y"}


def _word_log(message: str) -> None:
    if _WORD_VERBOSE:
        print(message)


def _source_signature(source_path: Path) -> tuple[str, int, int]:
    stat = source_path.stat()
    return str(source_path.resolve()), int(stat.st_mtime_ns), int(stat.st_size)


def _get_word_app():
    global _WORD_APP
    if _WORD_REUSE and _WORD_APP is not None:
        return _WORD_APP
    _WORD_APP = start_word_app(log_callback=_word_log)
    return _WORD_APP


def _shutdown_word(force: bool = False) -> None:
    global _WORD_APP
    if _WORD_APP is None:
        return
    if _WORD_REUSE and not force:
        return
    try:
        try:
            shutdown_word_app(_WORD_APP, log_callback=_word_log)
        except TypeError:
            shutdown_word_app(_WORD_APP)
    except Exception:
        pass
    _WORD_APP = None


def cleanup_temp_files() -> None:
    for path in list(_TEMP_FILES):
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass
    _shutdown_word(force=True)


atexit.register(cleanup_temp_files)


def convert_doc_to_docx(source_path: Path, *, target_dir: Path | None = None) -> Path:
    source_path = source_path.resolve()
    key, mtime_ns, size = _source_signature(source_path)
    cached = _CONVERT_CACHE.get(key)
    if cached and cached[0] == mtime_ns and cached[1] == size and cached[2].exists():
        if _WORD_VERBOSE:
            print(f"[wordcom] convert cache hit: {source_path.name}")
        return cached[2]

    ts_start = time.perf_counter()
    target_dir = target_dir or (Path(tempfile.gettempdir()) / "dashboard_core_converted")
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{source_path.stem}_{int(time.time() * 1000)}_{os.getpid()}.docx"

    safe_source = source_path
    try:
        str(source_path).encode("ascii")
    except UnicodeEncodeError:
        temp_dir = Path(tempfile.gettempdir()) / "dashboard_core_inputs"
        temp_dir.mkdir(parents=True, exist_ok=True)
        safe_source = temp_dir / source_path.name
        if not safe_source.exists():
            safe_source.write_bytes(source_path.read_bytes())

    document = None
    try:
        word = _get_word_app()
        document = open_document(word, str(safe_source), read_only=True)
        document.SaveAs2(str(target_path), FileFormat=WORD_SAVE_AS_DOCX)
    except WordComError as error:
        raise RuntimeError("Не вдалося конвертувати документ через Word COM.") from error
    finally:
        if document is not None:
            document.Close(False)
        _shutdown_word()

    if target_dir == Path(tempfile.gettempdir()) / "dashboard_core_converted":
        _TEMP_FILES.append(target_path)
    _CONVERT_CACHE[key] = (mtime_ns, size, target_path)
    if _WORD_VERBOSE:
        elapsed = time.perf_counter() - ts_start
        print(f"[wordcom] convert done {source_path.name} in {elapsed:.2f}s")
    return target_path
