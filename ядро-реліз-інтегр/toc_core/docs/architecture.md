# Архітектура

## Модулі
- `outline_parser.py` — швидке читання структури з docx (без Word COM).
- `manifest_reader.py` — читання `manifest.json` і витяг `free_listener`.
- `table_builder.py` — перетворення секцій на рядки таблиці.
- `word_com.py` — мінімальна автоматизація Word (вставка таблиці, заповнення, збереження).
- `main.py` / `gui.py` — CLI + GUI.

## Потік даних
1. `outline_parser.parse_outline()` читає `word/document.xml` і `word/styles.xml`.
2. `outline_parser.build_sections()` формує структуру секцій/доповідей.
3. `manifest_reader.load_free_listeners()` додає список `free_listener` і заголовок блоку з `sections_path` або fallback.
4. `table_builder.build_rows()` будує рядки таблиці, включно з окремим `free_listeners_header`.
5. `word_com` вставляє таблицю з `Table.docx` та заповнює її.

## Стилі TOC
- `section` / `Tab_SEC` — назви секцій і заголовок блоку вільних слухачів.
- `authors` / `Tab_PIP` — автори та список вільних слухачів.
- `title` / `Tab_Taitl` — назви доповідей.

## Word COM
Word COM використовується тільки для вставки таблиці і форматування. Усі структурні дані беруться з `docx` напряму.
