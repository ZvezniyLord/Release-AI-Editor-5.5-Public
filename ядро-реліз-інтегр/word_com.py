from __future__ import annotations

import atexit
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
        word.Visible = False
        word.DisplayAlerts = 0
        _ = word.Documents.Count
    except Exception:
        pass


def start_word_app(log_callback=None, attempts: int = 4, delay_sec: float = 0.75):
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
                return word
            except Exception:
                word = None
            if log_callback is not None:
                log_callback(f"[wordcom] запуск Word COM (спроба {attempt}/{attempts})")
            word = win32com.client.DispatchEx("Word.Application")
            _warmup_word(word)
            word.Visible = False
            word.DisplayAlerts = 0
            pid = _get_pid_from_word(word)
            if pid:
                _STARTED_PIDS.add(pid)
            return word
        except Exception as error:
            last_error = error
            word = None
            if log_callback is not None:
                log_callback(f"[wordcom] Word COM не запустився ({error}), повтор...")
                log_callback(f"[wordcom] очікую {delay_sec:.2f}с перед повтором")
            try:
                word = win32com.client.Dispatch("Word.Application")
                _warmup_word(word)
                pid = _get_pid_from_word(word)
                if pid:
                    _STARTED_PIDS.add(pid)
                return word
            except Exception:
                word = None
            time.sleep(delay_sec)
    raise WordComError("Не вдалося запустити Word COM") from last_error


def open_document_from_template(word, template_path: str):
    try:
        return word.Documents.Add(Template=template_path, NewTemplate=False, DocumentType=0)
    except Exception as error:
        raise WordComError("Не вдалося відкрити шаблон у Word COM") from error


def open_document(
    word,
    source_path: str,
    read_only: bool = True,
    open_and_repair: bool = False,
):
    try:
        return word.Documents.Open(
            source_path,
            ConfirmConversions=False,
            ReadOnly=read_only,
            AddToRecentFiles=False,
            OpenAndRepair=open_and_repair,
            Visible=False,
        )
    except Exception as error:
        raise WordComError("Не вдалося відкрити документ у Word COM") from error


def shutdown_word_app(word) -> None:
    try:
        if word is not None:
            word.Quit()
    finally:
        pythoncom.CoUninitialize()


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
