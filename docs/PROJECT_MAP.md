# PROJECT_MAP

## Призначення проєкту
Release AI Editor — це набір модулів для складання наукового журналу з папки заявок і Excel‑реєстру учасників. Система сканує Word‑документи, зіставляє їх з назвами статей, збирає чернетку журналу через Word COM, генерує дашборд та технічні звіти, а також виконує нормалізацію стилів, авторів, назв і змісту.

## Архітектурний огляд
Проєкт складається з трьох ядер:
- `ядро-реліз-інтегр/` — основний автономний пайплайн: дашборд → переміщення → нормалізація → чернетка → автори/назви → зміст.
- `ядро GPT Super Табел/` — окреме ядро побудови таблиці змісту (TOC).
- `ядро-реліз/` — legacy-ядро (старіший шлях, використовується рідко).

## Опис ключових модулів
### 1) Основне ядро (`ядро-реліз-інтегр`)
- `launcher.py` — головний GUI/CLI‑запуск пайплайну.
- `dashboard_core/` — підготовка даних, дашборд, JSON.
- `core/` — relocate/normalize/draft/titles/authors/toc та інші CLI‑утиліти.
- `draft_core/` — вставка статей у чернетку через Word COM + контроль references.
- `shapka_core/` — розбір “шапки” (автори/UDC/службові рядки).
- `toc_core/` — генерація TOC з шаблону `Table.docx`.
- `shared/` — спільні утиліти Word COM та shutdown‑логіка.
- `resources/` — markers.json, style_registry.json, name_sektsii.json.
- `assets/templates/` — `Jurnal.dotx`, `Table.docx`.

### 2) TOC‑ядро (`ядро GPT Super Табел`)
Самостійний набір скриптів для побудови таблиці змісту, який може запускатися окремо.

### 3) Legacy‑ядро (`ядро-реліз`)
Старіший автономний шлях (дашборд, relocate, чернетка).

## Виконання: основний runtime‑потік (ядро‑реліз‑інтегр)
1. Вхід: папка заявок + Excel учасників.
2. `dashboard_core.prepare_run()` → `matches.json`, `manifest.json`, `dashboard_perevirky.xlsx`.
3. `core.relocate_articles` → `run_dir/Статті`.
4. `core.normalize_folder` → `run_dir/Статті_норм` (parse → normalize → rebuild).
5. `draft_core.word_draft_builder` → `draft_journal.docx`.
6. `core.normalize_authors` / `core.normalize_titles` → стилі `AUTOR`/`Назва1`.
7. `core.toc_main` → TOC у `draft_journal_зміст.docx` (за потреби).

## Ключові маркери системи
- Маркери контенту: UDC/УДК, Abstract/Анотація, Keywords/Ключові слова, References/Список джерел.
- Правило пробілів: **після Keywords один порожній абзац**, **після анотації порожніх абзаців не допускається**.
- Плейсхолдери: `<<CHART_PLACEHOLDER_N>>`, `<<IMG_PLACEHOLDER_N>>`.
- Стилі: `SECTION`, `AUTOR`, `Назва1`, `REFER`, `REF-TITLE`, `TABLETEXT`, `Tab_*`.
- Артефакти: `matches.json`, `manifest.json`, `summary.json`, `diagnostics.json`, `draft_journal.docx`, `dashboard_perevirky.xlsx`.
