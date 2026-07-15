# KEYWORDS_AND_MARKERS

## Системні маркери контенту
- **UDC/УДК** — пошук класифікації.
- **Анотація/Abstract/Annotation** — початок анотації.
- **Ключові слова/Keywords/Key words** — початок блоку ключових слів.
- **References/Список використаних джерел/Література** — заголовок references.

## Маркери у resources/markers.json (`ядро-реліз-інтегр`)
- `annotation_markers`, `keyword_markers`, `reference_markers`.
- `author_stop_markers`, `author_exclude_markers`.
- `non_article_markers`, `non_article_text_markers`.
- Для `reference_markers` слід враховувати і пошкоджені/змішані префікси, зокрема латинську `C` у `Cписок`, бо такі варіанти реально трапляються у вхідних DOCX.

## Службові плейсхолдери
- `<<CHART_PLACEHOLDER_N>>` — плейсхолдер для Chart (переноситься COM‑копіюванням).
- `<<IMG_PLACEHOLDER_N>>` — плейсхолдер для нечитабельних зображень.

## Стилі (style_registry.json)
- `SECTION` / `СЕКЦІЯ заголовок` / `Heading 1` — стиль секції.
- `AUTHOR` / `Heading 2` — стиль автора.
- `TITLE` / `Heading 3` — стиль назви.
- `UDC` — стиль класифікації.
- `REFER` / `REF-TITLE` — стиль references.
- `Tab_SEC`, `Tab_PIP`, `Tab_Taitl`, `tablenumber` — стилі TOC.
- `TABLETEXT` — текст у таблицях після нормалізації.
- `AUTOR`, `Назва1` — службові стилі пост‑обробки у чернетці.

## Ключові ідентифікатори у JSON/виходах
- `matches.json`, `manifest.json`, `summary.json`, `diagnostics.json`.
- `draft_journal.docx`, `dashboard_perevirky.xlsx`.

## Повторювані патерни назв
- `*_cleaned_YYYYMMDD_HHMMSS.docx` — нормалізовані документи.
- `*_release_YYYYMMDD_HHMMSS.docx` — release‑версія журналу.
- `run_dir/Статті`, `run_dir/Статті_норм` — робочі каталоги інтегрованого ядра.

## Часті ключові слова у коді
- `prepare_run`, `relocate`, `normalize_docx`, `build_draft`.
- `normalize_annotation_markers`, `normalize_reference_markers`.
