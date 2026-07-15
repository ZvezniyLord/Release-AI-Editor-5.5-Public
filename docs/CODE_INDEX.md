# CODE_INDEX

## Корінь репозиторію
- `README.md` — короткий опис.
- `docs/README.md` — вхідна документація.
- `AGENTS.md` — інструкції для агентів.
- `AGENT_CONTEXT.md` — короткий контекст.
- `APPROACH.md` — правила нормалізації Word‑документів.
- `requirements.txt` — залежності верхнього рівня.

## Основне ядро (`ядро-реліз-інтегр`)
- `launcher.py` — головний GUI/CLI‑запуск.
- `dashboard_core/` — підготовка дашборду та JSON.
- `core/` — relocate/normalize/draft/titles/authors/toc.
- `draft_core/` — збірка чернетки через Word COM.
- `shapka_core/` — аналіз “шапки” статей (автори/UDC).
- `toc_core/` — генерація TOC.
- `shared/` — Word COM, safe shutdown, логування.
- `resources/` — markers.json, style_registry.json, name_sektsii.json.
- `assets/templates/` — `Jurnal.dotx`, `Table.docx`.

## TOC‑ядро (`ядро GPT Super Табел`)
- `main.py`, `gui.py`, `outline_parser.py`, `table_builder.py` — побудова TOC.

## Legacy‑ядро (`ядро-реліз`)
- `launcher.py` — старіший автономний запуск.
- `core/` — старіша логіка relocate/draft/dashboard.
## Single Article
- `ядро-реліз-інтегр/core/normalize_single_article.py` — нормалізація одного документа з ручним введенням назви статті.
- `ядро-реліз-інтегр/core/normalize_caption_layout.py` — нормалізація підписів таблиць/рисунків і порожніх абзаців навколо них.
- `ядро-реліз-інтегр/core/block_handlers/caption_block.py` — інтеграція обробки підписів у блоковий пайплайн.
- `ядро-реліз-інтегр/dashboard_core/io/excel_reader.py` — читання Excel і мапінг секцій за довідником `name_sektsii.json` (включно з нормалізацією префіксів та варіантів назв).
