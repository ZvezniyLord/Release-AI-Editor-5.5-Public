from __future__ import annotations

import atexit
import signal
import sys
import threading
from typing import Callable

from safe_shutdown import safe_shutdown

_cleanup_lock = threading.Lock()
_cleanup_done = False


def _run_cleanup(log_callback=None) -> None:
    global _cleanup_done
    with _cleanup_lock:
        if _cleanup_done:
            return
        _cleanup_done = True
    safe_shutdown(log_callback=log_callback)


def install_cleanup_hooks(log_callback=None) -> None:
    def _atexit_handler() -> None:
        _run_cleanup(log_callback=log_callback)

    def _signal_handler(signum, _frame) -> None:
        _run_cleanup(log_callback=log_callback)
        raise SystemExit(1)

    def _excepthook(exc_type, exc, tb) -> None:
        _run_cleanup(log_callback=log_callback)
        sys.__excepthook__(exc_type, exc, tb)

    atexit.register(_atexit_handler)
    sys.excepthook = _excepthook
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _signal_handler)
        except Exception:
            continue
