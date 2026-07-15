from __future__ import annotations

import atexit
import os
import time
from typing import Optional

import pythoncom
import win32com.client
import win32process
import win32api


class WordComError(RuntimeError):
    pass


_STARTED_PIDS: set[int] = set()
_WARMUP_WORD = None


def _is_verbose() -> bool:
    return os.getenv("WORD_COM_VERBOSE", "").strip().lower() in {"1", "true", "yes", "y"}


def _is_visible() -> bool:
    return os.getenv("WORD_COM_VISIBLE", "").strip().lower() in {"1", "true", "yes", "y"}


def _emit(log_callback, message: str) -> None:
    if log_callback is not None:
        log_callback(message)
    elif _is_verbose():
        print(message)


def _get_pid_from_word(word) -> Optional[int]:
    try:
        hwnd = int(word.Hwnd)
    except Exception:
        return None
    try:
        _tid, pid = win32process.GetWindowThreadProcessId(hwnd)
        return int(pid)
    except Exception:
        return None


def _warmup_word(word) -> None:
    try:
        word.Visible = bool(_is_visible())
        word.DisplayAlerts = 0
        _ = word.Documents.Count
    except Exception:
        pass


def start_word_app(log_callback=None, attempts: int = 4, delay_sec: float = 0.75):
    ts_start = time.perf_counter()
    pythoncom.CoInitialize()
    last_error = None
    word = None
    for attempt in range(1, attempts + 1):
        try:
            try:
                word = win32com.client.GetActiveObject("Word.Application")
                _warmup_word(word)
                pid = _get_pid_from_word(word)
                if pid:
                    _STARTED_PIDS.add(pid)
                if _is_verbose():
                    _emit(log_callback, f"[wordcom] reuse active Word PID={pid or '-'}")
                return word
            except Exception:
                word = None
            _emit(log_callback, f"[wordcom] запуск Word COM (спроба {attempt}/{attempts})")
            word = win32com.client.DispatchEx("Word.Application")
            _warmup_word(word)
            word.Visible = bool(_is_visible())
            word.DisplayAlerts = 0
            pid = _get_pid_from_word(word)
            if pid:
                _STARTED_PIDS.add(pid)
            if _is_verbose():
                elapsed = time.perf_counter() - ts_start
                _emit(log_callback, f"[wordcom] started PID={pid or '-'} in {elapsed:.2f}s")
            return word
        except Exception as error:
            last_error = error
            word = None
            _emit(log_callback, f"[wordcom] Word COM не запустився ({error}), повтор...")
            _emit(log_callback, f"[wordcom] очікую {delay_sec:.2f}с перед повтором")
            try:
                word = win32com.client.Dispatch("Word.Application")
                _warmup_word(word)
                pid = _get_pid_from_word(word)
                if pid:
                    _STARTED_PIDS.add(pid)
                if _is_verbose():
                    elapsed = time.perf_counter() - ts_start
                    _emit(log_callback, f"[wordcom] fallback started PID={pid or '-'} in {elapsed:.2f}s")
                return word
            except Exception:
                word = None
            time.sleep(delay_sec)
    raise WordComError("Не вдалося запустити Word COM") from last_error


def open_document_from_template(word, template_path: str):
    ts_start = time.perf_counter()
    try:
        doc = word.Documents.Add(Template=template_path, NewTemplate=False, DocumentType=0)
        if _is_verbose():
            elapsed = time.perf_counter() - ts_start
            print(f"[wordcom] open template {template_path} in {elapsed:.2f}s")
        return doc
    except Exception as error:
        raise WordComError("Не вдалося відкрити шаблон у Word COM") from error


def open_document(word, source_path: str, read_only: bool = True, open_and_repair: bool = False):
    ts_start = time.perf_counter()
    try:
        doc = word.Documents.Open(
            source_path,
            ReadOnly=read_only,
            AddToRecentFiles=False,
            OpenAndRepair=open_and_repair,
        )
        if _is_verbose():
            elapsed = time.perf_counter() - ts_start
            print(f"[wordcom] open doc {source_path} in {elapsed:.2f}s")
        return doc
    except Exception as error:
        raise WordComError("Не вдалося відкрити документ у Word COM") from error


def shutdown_word_app(word, log_callback=None) -> None:
    ts_start = time.perf_counter()
    try:
        if word is not None:
            if _is_verbose():
                pid = _get_pid_from_word(word)
                _emit(log_callback, f"[wordcom] quit Word PID={pid or '-'}")
            word.Quit()
    finally:
        pythoncom.CoUninitialize()
        if _is_verbose():
            elapsed = time.perf_counter() - ts_start
            _emit(log_callback, f"[wordcom] shutdown complete in {elapsed:.2f}s")


def shutdown_started_word_processes(log_callback=None) -> None:
    # Close only processes we started
    for pid in list(_STARTED_PIDS):
        try:
            handle = win32api.OpenProcess(1, False, pid)
            win32api.TerminateProcess(handle, 0)
            _STARTED_PIDS.discard(pid)
            if log_callback:
                log_callback(f"[wordcom] завершено Word PID {pid}")
        except Exception:
            continue


def warmup_word(template_path: str | None = None, log_callback=None, keep_open: bool = True):
    """Start Word COM early to avoid first-call failures."""
    global _WARMUP_WORD
    word = start_word_app(log_callback=log_callback)
    if template_path:
        try:
            doc = open_document_from_template(word, template_path)
            doc.Close(False)
        except Exception:
            pass
    if keep_open:
        _WARMUP_WORD = word
        return word
    shutdown_word_app(word)
    return None


atexit.register(shutdown_started_word_processes)
