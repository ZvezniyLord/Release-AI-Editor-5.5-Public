from __future__ import annotations

from word_com import shutdown_started_word_processes


def safe_shutdown(log_callback=None) -> None:
    shutdown_started_word_processes(log_callback=log_callback)
