from __future__ import annotations

import os
import sys

try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog
except Exception:  # pragma: no cover - optional GUI
    tk = None
    messagebox = None
    simpledialog = None


def _use_tty() -> bool:
    try:
        return sys.stdin is not None and sys.stdin.isatty()
    except Exception:
        return False


def _auto_yes() -> bool:
    return os.getenv("AI_EDITOR_ACCEPT_ALL", "").strip().lower() in {"1", "true", "yes", "y"}


def _safe_input(prompt: str) -> str | None:
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        return None


def ask_yes_no(message: str, *, title: str = "Підтвердження") -> bool:
    if _auto_yes():
        return True
    if _use_tty():
        raw = _safe_input(f"{message}\n(y/n): ")
        if raw is None:
            return False
        answer = raw.strip().lower()
        return answer in {"y", "yes", "так", "t", "1"}
    if tk is None or messagebox is None:
        return False
    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    try:
        return messagebox.askyesno(title, message, parent=root)
    finally:
        root.destroy()


def _ask_multiline_text_gui(message: str, *, title: str, default: str, width: int = 90, height: int = 12) -> str | None:
    if tk is None:
        return default or None
    root = tk.Tk()
    root.withdraw()
    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.transient(root)
    dialog.grab_set()
    try:
        dialog.attributes("-topmost", True)
    except Exception:
        pass
    dialog.geometry("900x360")
    dialog.columnconfigure(0, weight=1)
    dialog.rowconfigure(1, weight=1)

    tk.Label(dialog, text=message, anchor="w", justify="left").grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
    text = tk.Text(dialog, width=width, height=height, wrap="word")
    text.grid(row=1, column=0, sticky="nsew", padx=10, pady=6)
    if default:
        text.insert("1.0", default)

    result = {"value": None}

    def _ok() -> None:
        value = text.get("1.0", tk.END).strip()
        result["value"] = value or (default if default else "")
        dialog.destroy()

    def _cancel() -> None:
        result["value"] = None
        dialog.destroy()

    actions = tk.Frame(dialog)
    actions.grid(row=2, column=0, sticky="e", padx=10, pady=(6, 10))
    tk.Button(actions, text="OK", width=10, command=_ok).pack(side="left", padx=(0, 6))
    tk.Button(actions, text="Cancel", width=10, command=_cancel).pack(side="left")
    dialog.protocol("WM_DELETE_WINDOW", _cancel)
    dialog.wait_window()
    root.destroy()
    value = result["value"]
    if value is None:
        return None
    value = value.strip()
    if not value and default:
        return default
    return value


def ask_text(message: str, *, title: str = "Ввід", default: str = "", multiline: bool = False) -> str | None:
    if _auto_yes():
        return default
    if _use_tty():
        prompt = f"{message}"
        if default:
            prompt += f" [{default}]"
        prompt += ": "
        raw = _safe_input(prompt)
        if raw is None:
            return default or None
        answer = raw.strip()
        if not answer and default:
            return default
        return answer
    if tk is None or simpledialog is None:
        return default or None
    if multiline:
        return _ask_multiline_text_gui(message, title=title, default=default)
    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    try:
        result = simpledialog.askstring(title, message, initialvalue=default, parent=root)
        if result is None:
            return None
        result = result.strip()
        if not result and default:
            return default
        return result
    finally:
        root.destroy()
