# -*- coding: utf-8 -*-
import os
import json
import subprocess
import threading
import tkinter as tk
import importlib.util
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
import sys
import re
from tkinter import ttk

MODULE_ROOT = Path(__file__).resolve().parent
PYTHON = Path(sys.executable)
STATE_PATH = MODULE_ROOT / "launcher_state.json"
JOURNAL_TEMPLATE_PATH = MODULE_ROOT / "assets" / "templates" / "Jurnal.dotx"
TOC_TEMPLATE_PATH = MODULE_ROOT / "assets" / "templates" / "Table.docx"
FROZEN = bool(getattr(sys, "frozen", False))
INTERNAL_SCRIPT_FLAG = "--run-script"


def _load_script_module(script_rel_path: str):
    script_path = (MODULE_ROOT / script_rel_path).resolve()
    if not script_path.exists():
        raise FileNotFoundError(f"Не знайдено скрипт: {script_path}")
    module_name = re.sub(r"[^0-9A-Za-z_]+", "_", script_rel_path)
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Не вдалося завантажити скрипт: {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_internal_script(script_rel_path: str, script_args: list[str]) -> int:
    module = _load_script_module(script_rel_path)
    entrypoint = getattr(module, "main", None)
    if not callable(entrypoint):
        raise RuntimeError(f"У скрипті немає main(): {script_rel_path}")
    old_argv = sys.argv[:]
    try:
        sys.argv = [str((MODULE_ROOT / script_rel_path).resolve()), *script_args]
        entrypoint()
    finally:
        sys.argv = old_argv
    return 0


def _build_python_command(script_rel_path: str, *script_args: str) -> list[str]:
    if FROZEN:
        return [str(PYTHON), INTERNAL_SCRIPT_FLAG, script_rel_path, *script_args]
    return [str(PYTHON), str(MODULE_ROOT / script_rel_path), *script_args]


def _run_command(
    cmd: list[str],
    output: tk.Text,
    progress: ttk.Progressbar,
    progress_label: tk.Label,
    *,
    live_output: bool = True,
    word_visible: bool = False,
) -> None:
    progress_state = {
        "mode": None,
        "current": 0,
        "total": 0,
    }

    def _reset_progress():
        progress_state["mode"] = None
        progress_state["current"] = 0
        progress_state["total"] = 0
        progress_label.config(text="")
        try:
            progress.stop()
        except Exception:
            pass
        progress.config(mode="determinate")
        progress["value"] = 0
        progress["maximum"] = 1

    def _start_indeterminate():
        progress_state["mode"] = "indeterminate"
        progress_label.config(text="...")
        progress.config(mode="indeterminate")
        try:
            progress.start(12)
        except Exception:
            pass

    def _update_progress_from_line(line: str) -> bool:
        line = line.strip()
        if not line:
            return False
        patterns = [
            (r"\[(?:draft|relocate|shapka)\]\s*(\d+)\s*/\s*(\d+)", "draft"),
            (r"\[normalize\]\s*(\d+)\s*/\s*(\d+)", "normalize"),
            (r"\[normalize\]\s*file\s*(\d+)\s*/\s*(\d+)", "normalize_file"),
            (r"\[shapka\]\s*file\s*(\d+)\s*/\s*(\d+)", "shapka_files"),
            (r"\[prep\]\s*(\d+)\s*/\s*(\d+)", "prep"),
            (r"\[match\]\s*(\d+)\s*/\s*(\d+)", "match"),
        ]
        for pattern, mode in patterns:
            match = re.search(pattern, line)
            if not match:
                continue
            current = int(match.group(1))
            total = int(match.group(2))
            if total <= 0:
                return False
            if progress_state["mode"] != "determinate":
                try:
                    progress.stop()
                except Exception:
                    pass
                progress.config(mode="determinate")
            progress_state["mode"] = mode
            progress_state["current"] = current
            progress_state["total"] = total
            progress["maximum"] = total
            progress["value"] = current
            progress_label.config(text=f"{current}/{total}")
            return True
        return False
    def _append_output(text: str) -> None:
        output.insert(tk.END, text)
        output.see(tk.END)

    def worker():
        try:
            output.after(0, _reset_progress)
            output.after(0, _start_indeterminate)
            output.after(0, lambda: _append_output(f"$ {' '.join(cmd)}\n"))
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            if live_output:
                env["PYTHONUNBUFFERED"] = "1"
            else:
                env.pop("PYTHONUNBUFFERED", None)
            env["WORD_COM_VISIBLE"] = "1" if word_visible else "0"
            cmd_to_run = list(cmd)
            # Force unbuffered Python output when running scripts via launcher
            if live_output and len(cmd_to_run) >= 2 and Path(cmd_to_run[0]).name.lower().startswith("python") and cmd_to_run[1] != "-u":
                cmd_to_run.insert(1, "-u")
            proc = subprocess.Popen(
                cmd_to_run,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
            )
            for line in proc.stdout:
                def _handle(raw: str = line) -> None:
                    if not _update_progress_from_line(raw):
                        _append_output(raw)
                output.after(0, _handle)
            proc.wait()
            output.after(0, lambda: _append_output(f"[exit] {proc.returncode}\n"))
            output.after(0, _reset_progress)
        except Exception as error:
            output.after(0, lambda: _append_output(f"[error] {error}\n"))
            output.after(0, _reset_progress)

    threading.Thread(target=worker, daemon=True).start()


def _find_latest_run_dir(root: Path) -> Path | None:
    if not root.exists():
        return None
    dirs = [p for p in root.iterdir() if p.is_dir()]
    if not dirs:
        return None
    dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return dirs[0]


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _existing_or_default(raw_path: str | None, default_path: Path) -> str:
    if raw_path:
        try:
            candidate = Path(str(raw_path))
            if candidate.exists():
                return str(candidate)
        except Exception:
            pass
    return str(default_path)


def _save_state(state: dict) -> None:
    try:
        STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def main() -> None:
    root = tk.Tk()
    root.title("Ядро-Реліз Інтегр")
    root.minsize(900, 650)
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=1)
    root.columnconfigure(2, weight=1)

    state = _load_state()

    tk.Label(root, text="Цільова папка (учасники/заявки)").grid(row=0, column=0, sticky="w", padx=6, pady=4)
    target_var = tk.StringVar(value=state.get("target", ""))
    tk.Entry(root, textvariable=target_var, width=70).grid(row=0, column=1, padx=6, pady=4, sticky="ew")
    tk.Button(root, text="...", command=lambda: target_var.set(filedialog.askdirectory() or "")).grid(row=0, column=2, padx=6, pady=4, sticky="ew")

    tk.Label(root, text="Робоча папка (output root)").grid(row=1, column=0, sticky="w", padx=6, pady=4)
    output_root_var = tk.StringVar(value=state.get("output_root", str(MODULE_ROOT / "output")))
    tk.Entry(root, textvariable=output_root_var, width=70).grid(row=1, column=1, padx=6, pady=4, sticky="ew")
    tk.Button(root, text="...", command=lambda: output_root_var.set(filedialog.askdirectory() or "")).grid(row=1, column=2, padx=6, pady=4, sticky="ew")

    tk.Label(root, text="Ім'я run (slug)").grid(row=2, column=0, sticky="w", padx=6, pady=4)
    run_name_var = tk.StringVar(value=state.get("run_name", "zhurnal"))
    tk.Entry(root, textvariable=run_name_var, width=70).grid(row=2, column=1, padx=6, pady=4, sticky="ew")
    tk.Button(root, text="Останній run_dir", command=lambda: run_dir_var.set(str(_find_latest_run_dir(Path(output_root_var.get())) or ""))).grid(row=2, column=2, padx=6, pady=4, sticky="ew")

    stats_var = tk.BooleanVar(value=bool(state.get("stats", True)))
    tk.Checkbutton(root, text="Додати вкладку статистики", variable=stats_var).grid(row=3, column=0, sticky="w", padx=6, pady=4)

    interactive_match_var = tk.BooleanVar(value=bool(state.get("interactive_match", False)))
    tk.Checkbutton(root, text="Інтерактив: підтвердження кандидатів (10-80)", variable=interactive_match_var).grid(row=3, column=1, sticky="w", padx=6, pady=4)

    interactive_add_unknown_var = tk.BooleanVar(value=bool(state.get("interactive_add_unknown", False)))
    tk.Checkbutton(root, text="Інтерактив: додавання відсутніх в Excel", variable=interactive_add_unknown_var).grid(row=3, column=2, sticky="w", padx=6, pady=4)
    word_visible_var = tk.BooleanVar(value=bool(state.get("word_visible", False)))
    tk.Checkbutton(root, text="Видимий Word (COM)", variable=word_visible_var).grid(row=4, column=2, sticky="w", padx=6, pady=4)

    tk.Label(root, text="Інтерактив min/max score").grid(row=4, column=0, sticky="w", padx=6, pady=4)
    interactive_min_var = tk.StringVar(value=str(state.get("interactive_min_score", "10")))
    interactive_max_var = tk.StringVar(value=str(state.get("interactive_max_score", "80")))
    tk.Entry(root, textvariable=interactive_min_var, width=10).grid(row=4, column=1, padx=6, pady=4, sticky="w")
    tk.Entry(root, textvariable=interactive_max_var, width=10).grid(row=4, column=1, padx=(80, 6), pady=4, sticky="w")

    # Налаштування вирівнювання назв перенесено в нормалізацію статей

    tk.Label(root, text="run_dir").grid(row=5, column=0, sticky="w", padx=6, pady=4)
    run_dir_var = tk.StringVar(value=state.get("run_dir", ""))
    tk.Entry(root, textvariable=run_dir_var, width=70).grid(row=5, column=1, padx=6, pady=4, sticky="ew")
    tk.Button(root, text="...", command=lambda: run_dir_var.set(filedialog.askdirectory() or "")).grid(row=5, column=2, padx=6, pady=4, sticky="ew")

    tk.Label(root, text="Чернетка (docx)").grid(row=6, column=0, sticky="w", padx=6, pady=4)
    draft_var = tk.StringVar(value=state.get("draft", ""))
    tk.Entry(root, textvariable=draft_var, width=70).grid(row=6, column=1, padx=6, pady=4, sticky="ew")
    tk.Button(root, text="...", command=lambda: draft_var.set(filedialog.askopenfilename() or "")).grid(row=6, column=2, padx=6, pady=4, sticky="ew")

    tk.Label(root, text="Шаблон таблиці (Table.docx)").grid(row=7, column=0, sticky="w", padx=6, pady=4)
    toc_template_var = tk.StringVar(value=_existing_or_default(state.get("toc_template"), TOC_TEMPLATE_PATH))
    tk.Entry(root, textvariable=toc_template_var, width=70).grid(row=7, column=1, padx=6, pady=4, sticky="ew")
    tk.Button(root, text="...", command=lambda: toc_template_var.set(filedialog.askopenfilename() or "")).grid(row=7, column=2, padx=6, pady=4, sticky="ew")

    def _update_journal_template(journal_var: tk.StringVar):
        path = filedialog.askopenfilename(
            filetypes=[("Word template", "*.dotx"), ("Word documents", "*.docx"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            import shutil

            shutil.copy2(path, JOURNAL_TEMPLATE_PATH)
        except Exception:
            messagebox.showerror("Помилка", "Не вдалося оновити шаблон.")
            return
        journal_var.set(str(JOURNAL_TEMPLATE_PATH))
        output.insert(tk.END, f"[template] Оновлено шаблон журналу: {JOURNAL_TEMPLATE_PATH}\n")
        output.see(tk.END)

    tk.Label(root, text="Шаблон журналу (Jurnal.dotx)").grid(row=8, column=0, sticky="w", padx=6, pady=4)
    journal_template_var = tk.StringVar(value=str(JOURNAL_TEMPLATE_PATH))
    tk.Entry(root, textvariable=journal_template_var, width=70).grid(row=8, column=1, padx=6, pady=4, sticky="ew")
    tk.Button(root, text="Оновити шаблон журналу", command=lambda: _update_journal_template(journal_template_var)).grid(
        row=8, column=2, padx=6, pady=4, sticky="ew"
    )

    output_row = 12
    progress_frame = tk.Frame(root)
    progress_frame.grid(row=output_row, column=0, columnspan=3, padx=6, pady=(6, 0), sticky="ew")
    progress_frame.columnconfigure(0, weight=1)

    progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate", length=400)
    progress.grid(row=0, column=0, sticky="ew")
    progress_label = tk.Label(progress_frame, text="")
    progress_label.grid(row=1, column=0, sticky="w", pady=(2, 2))

    output = tk.Text(root, height=16, width=110)
    output.grid(row=output_row + 1, column=0, columnspan=3, padx=6, pady=6, sticky="nsew")
    root.rowconfigure(output_row + 1, weight=1)

    def force_kill_word():
        cmd = ["taskkill", "/F", "/IM", "WINWORD.EXE"]
        _run_command(cmd, output, progress, progress_label)

    def cleanup_runtime():
        run_dir = run_dir_var.get().strip()
        target = run_dir or output_root_var.get().strip()
        cmd = _build_python_command("core/cleanup_runtime.py")
        if target:
            cmd.append(target)
        _run_command(cmd, output, progress, progress_label)

    def _persist_state():
        _save_state({
            "target": target_var.get().strip(),
            "output_root": output_root_var.get().strip(),
            "run_name": run_name_var.get().strip(),
            "stats": bool(stats_var.get()),
            "interactive_match": bool(interactive_match_var.get()),
            "interactive_add_unknown": bool(interactive_add_unknown_var.get()),
            "word_visible": bool(word_visible_var.get()),
            "interactive_min_score": interactive_min_var.get().strip(),
            "interactive_max_score": interactive_max_var.get().strip(),
            "run_dir": run_dir_var.get().strip(),
            "draft": draft_var.get().strip(),
            "toc_template": toc_template_var.get().strip(),
        })

    def _persist_state_from_gui():
        _persist_state()

    def _on_close():
        _persist_state()
        root.destroy()

    def run_dashboard():
        target = target_var.get().strip()
        out_root = output_root_var.get().strip()
        run_name = run_name_var.get().strip() or "zhurnal"
        if not target:
            messagebox.showerror("Помилка", "Вкажи цільову папку")
            return
        if not out_root:
            messagebox.showerror("Помилка", "Вкажи робочу папку")
            return
        _persist_state()
        cmd = _build_python_command(
            "core/dashboard_main.py",
            target,
            "--output",
            out_root,
            "--name",
            run_name,
        )
        if stats_var.get():
            cmd.append("--stats")
        else:
            cmd.append("--no-stats")
        if interactive_match_var.get():
            cmd.append("--interactive-match")
            min_score = interactive_min_var.get().strip()
            max_score = interactive_max_var.get().strip()
            if min_score:
                cmd.extend(["--interactive-min-score", min_score])
            if max_score:
                cmd.extend(["--interactive-max-score", max_score])
        if interactive_add_unknown_var.get():
            cmd.append("--interactive-add-unknown")
        _run_command(cmd, output, progress, progress_label, live_output=True, word_visible=bool(word_visible_var.get()))

        def refresh():
            latest = _find_latest_run_dir(Path(out_root))
            if latest:
                run_dir_var.set(str(latest))
        root.after(1500, refresh)

    def run_relocate():
        run_dir = run_dir_var.get().strip()
        if not run_dir:
            run_dir = str(_find_latest_run_dir(Path(output_root_var.get().strip())) or "")
            run_dir_var.set(run_dir)
        if not run_dir:
            messagebox.showerror("Помилка", "Вкажи run_dir або output root")
            return
        _persist_state()
        cmd = _build_python_command(
            "core/relocate_main.py",
            run_dir,
            "--folder",
            "Статті",
        )
        _run_command(cmd, output, progress, progress_label, live_output=True, word_visible=bool(word_visible_var.get()))

    def run_normalize():
        run_dir = run_dir_var.get().strip()
        if not run_dir:
            run_dir = str(_find_latest_run_dir(Path(output_root_var.get().strip())) or "")
            run_dir_var.set(run_dir)
        if not run_dir:
            messagebox.showerror("Помилка", "Вкажи run_dir або output root")
            return
        _persist_state()
        cmd = _build_python_command(
            "core/normalize_main.py",
            run_dir,
            "--source-folder",
            "Статті",
            "--output-folder",
            "Статті_норм",
        )
        _run_command(cmd, output, progress, progress_label, live_output=True, word_visible=bool(word_visible_var.get()))

    def run_normalize_single_article():
        run_dir = run_dir_var.get().strip()
        if not run_dir:
            run_dir = str(_find_latest_run_dir(Path(output_root_var.get().strip())) or "")
            run_dir_var.set(run_dir)
        if not run_dir:
            messagebox.showerror("Помилка", "Вкажи run_dir або output root")
            return
        run_dir_path = Path(run_dir)
        source_dir = run_dir_path / "Статті"
        if not source_dir.exists():
            source_dir = run_dir_path

        source_file = filedialog.askopenfilename(
            title="Оберіть документ статті для нормалізації",
            initialdir=str(source_dir),
            filetypes=[("Word documents", "*.docx"), ("All files", "*.*")],
        )
        if not source_file:
            return

        title = simpledialog.askstring(
            "Назва статті",
            "Введіть назву статті (як при додаванні відсутньої в Excel):",
            parent=root,
        )
        if title is None or not title.strip():
            messagebox.showwarning("Увага", "Назва статті не введена.")
            return
        title = title.strip()

        output_dir = run_dir_path / "Статті_норм"
        output_path = output_dir / f"{Path(source_file).stem}.docx"

        _persist_state()
        cmd = _build_python_command(
            "core/normalize_single_article.py",
            source_file,
            "--title",
            title,
            "--output",
            str(output_path),
        )
        _run_command(cmd, output, progress, progress_label, live_output=True, word_visible=bool(word_visible_var.get()))

    def run_draft():
        run_dir = run_dir_var.get().strip()
        if not run_dir:
            run_dir = str(_find_latest_run_dir(Path(output_root_var.get().strip())) or "")
            run_dir_var.set(run_dir)
        if not run_dir:
            messagebox.showerror("Помилка", "Вкажи run_dir або output root")
            return
        _persist_state()
        cleanup_runtime()
        source_folder = Path(run_dir) / "Статті_норм"
        if not source_folder.exists():
            source_folder = Path(run_dir) / "Статті"
        output_name = "draft_journal.docx"
        cmd = _build_python_command(
            "core/draft_main.py",
            run_dir,
            "--skip-relocate",
            "--source-folder",
            str(source_folder),
            "--output",
            str(Path(run_dir) / output_name),
        )
        _run_command(cmd, output, progress, progress_label, live_output=True, word_visible=bool(word_visible_var.get()))
        draft_var.set(str(Path(run_dir) / output_name))

    def run_toc():
        draft_path = draft_var.get().strip()
        template_path = toc_template_var.get().strip()
        if not draft_path:
            messagebox.showerror("Помилка", "Вкажи шлях до чернетки")
            return
        if not template_path:
            messagebox.showerror("Помилка", "Вкажи шаблон Table.docx")
            return
        _persist_state()
        cleanup_runtime()
        manifest_path = ""
        candidate = Path(draft_path).with_name("manifest.json")
        if candidate.exists():
            manifest_path = str(candidate)
        output_path = Path(draft_path).with_name(Path(draft_path).stem + "_зміст.docx")
        cmd = _build_python_command(
            "core/toc_main.py",
            draft_path,
            "--output",
            str(output_path),
            "--template",
            template_path,
        )
        if manifest_path:
            cmd.extend(["--manifest", manifest_path])
        _run_command(cmd, output, progress, progress_label, live_output=True, word_visible=bool(word_visible_var.get()))

    btn_opts = {"pady": 3, "padx": 3, "sticky": "ew"}
    tk.Button(root, text="1. Створити дашборд", command=run_dashboard, width=30).grid(row=9, column=0, **btn_opts)
    tk.Button(root, text="2. Перемістити статті", command=run_relocate, width=30).grid(row=9, column=1, **btn_opts)
    tk.Button(root, text="3. Нормалізувати статті (всі блоки)", command=run_normalize, width=30).grid(row=9, column=2, **btn_opts)
    tk.Button(root, text="4. Зібрати чернетку", command=run_draft, width=30).grid(row=10, column=0, **btn_opts)
    tk.Button(root, text="5. Додати таблицю змісту", command=run_toc, width=30).grid(row=10, column=1, **btn_opts)
    tk.Button(root, text="Очистити Word/lock", command=cleanup_runtime, width=30).grid(row=10, column=2, **btn_opts)
    tk.Button(root, text="3b. Нормалізувати Статтю", command=run_normalize_single_article, width=30).grid(row=11, column=0, **btn_opts)
    tk.Button(root, text="Завершити Word", command=force_kill_word, width=30).grid(row=11, column=2, **btn_opts)

    # Persist on any change
    for var in (target_var, output_root_var, run_name_var, run_dir_var, draft_var, toc_template_var):
        var.trace_add("write", lambda *_: _persist_state_from_gui())
    for var in (stats_var, interactive_match_var, interactive_add_unknown_var, word_visible_var, interactive_min_var, interactive_max_var):
        var.trace_add("write", lambda *_: _persist_state_from_gui())

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == INTERNAL_SCRIPT_FLAG:
        raise SystemExit(_run_internal_script(sys.argv[2], sys.argv[3:]))
    main()
