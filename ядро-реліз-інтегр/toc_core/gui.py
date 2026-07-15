# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox


def run_gui(run_fn, default_template: Path) -> None:
    root = tk.Tk()
    root.title("GPT Super Табел")

    doc_var = tk.StringVar(value="")
    manifest_var = tk.StringVar(value="")
    template_var = tk.StringVar(value=str(default_template))

    tk.Label(root, text="Документ .docx").grid(row=0, column=0, sticky="w", padx=6, pady=4)
    tk.Entry(root, textvariable=doc_var, width=70).grid(row=0, column=1, padx=6, pady=4)
    tk.Button(root, text="...", command=lambda: doc_var.set(filedialog.askopenfilename() or "")).grid(row=0, column=2, padx=6, pady=4)

    tk.Label(root, text="manifest.json (необов'язково)").grid(row=1, column=0, sticky="w", padx=6, pady=4)
    tk.Entry(root, textvariable=manifest_var, width=70).grid(row=1, column=1, padx=6, pady=4)
    tk.Button(root, text="...", command=lambda: manifest_var.set(filedialog.askopenfilename() or "")).grid(row=1, column=2, padx=6, pady=4)

    tk.Label(root, text="Table.docx (шаблон)").grid(row=2, column=0, sticky="w", padx=6, pady=4)
    tk.Entry(root, textvariable=template_var, width=70).grid(row=2, column=1, padx=6, pady=4)
    tk.Button(root, text="...", command=lambda: template_var.set(filedialog.askopenfilename() or "")).grid(row=2, column=2, padx=6, pady=4)

    def run():
        value = doc_var.get().strip().strip('"')
        if not value:
            messagebox.showerror("Помилка", "Вкажи шлях до документа")
            return
        doc_path = Path(value)
        if not doc_path.exists():
            messagebox.showerror("Помилка", "Файл не знайдено")
            return
        manifest_value = manifest_var.get().strip().strip('"')
        manifest_path = Path(manifest_value) if manifest_value else None
        template_value = template_var.get().strip().strip('"')
        template_path = Path(template_value) if template_value else default_template
        if not template_path.exists():
            messagebox.showerror("Помилка", f"Шаблон не знайдено: {template_path}")
            return
        output_path = doc_path.with_name(f"{doc_path.stem}_зміст{doc_path.suffix}")
        try:
            run_fn(doc_path, output_path, template_path, manifest_path)
        except Exception as error:
            messagebox.showerror("Помилка", str(error))
            return
        messagebox.showinfo("Готово", f"Створено: {output_path}")

    tk.Button(root, text="Згенерувати таблицю", command=run).grid(row=3, column=0, columnspan=3, pady=8)
    root.mainloop()
