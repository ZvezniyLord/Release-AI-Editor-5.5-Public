# Аудит Version_5.5

Дата: 2026-05-04

## Що перевірено
- Архітектурна документація: `docs/PROJECT_MAP.md`, `docs/CODE_INDEX.md`, `docs/DEPENDENCY_MAP.md`, `docs/EXECUTION_FLOW.md`, `docs/KEYWORDS_AND_MARKERS.md`, `docs/MODULE_DESCRIPTIONS.md`, `AGENT_CONTEXT.md`.
- Основне інтегроване ядро: `ядро-реліз-інтегр`.
- Ресурси та шаблони: `resources/*.json`, `assets/templates/Jurnal.dotx`, `assets/templates/Table.docx`.
- Збірка PyInstaller через `build_exe.ps1`.
- Тести `dashboard_core` для мапінгу секцій та тести `toc_core`.

## Основні ризики, знайдені під час аудиту
- `launcher_state.json` містив абсолютні шляхи до конкретного запуску конференції 115 і старого розташування основного проекту. У збірці це могло відкривати GUI з неактуальними шляхами.
- `toc_core/main.py` мав default-шлях `toc_core/assets/templates/Table.docx`, але в інтегрованому ядрі шаблон лежить у `assets/templates/Table.docx`.
- У source-файлах були прямі mojibake-маркери для обробки пошкоджених вхідних документів. Функціонально це потрібно, але сам source краще тримати без `Рљ...`, `Рђ...`, `вЂ...`.
- Тести `toc_core/tests/test_manifest.py` відставали від актуального API `load_free_listeners`, який повертає `(header, names)`.
- Стара збірка/копія могла переносити `__pycache__` і debug JSON у дистрибутив через широкі `--add-data`.

## Що змінено тільки у Version_5.5
- GUI тепер підставляє локальний `assets/templates/Table.docx`, якщо збережений шлях відсутній або не існує.
- `launcher_state.json` очищено від шляхів до конференції 115 і основного проекту.
- Default TOC template виправлено на `ROOT.parent / "assets" / "templates" / "Table.docx"`.
- Mojibake-маркери в коді замінені на обчислення через UTF-8 -> CP1251, щоб source залишався чистим UTF-8.
- Оновлено тести `toc_core` під поточний API.
- Додано `pyinstaller` до requirements у копії.
- Перед фінальною збіркою прибрано copied debug JSON та source `__pycache__`.

## Перевірка
- `pytest dashboard_core/tests/test_excel_reader_sections.py toc_core/tests`: 12 passed.
- `compileall`: без помилок.
- PyInstaller build: успішно.
- Smoke-перевірка exe через `--run-script core/excel_validate.py --help`: exit code 0.

## Результат збірки
- EXE: `ядро-реліз-інтегр/dist/ReleaseAIEditor/ReleaseAIEditor.exe`
- Шаблони і ресурси включені в `_internal/assets/templates` та `_internal/resources`.
- `launcher_state.json` у `_internal` не містить абсолютних шляхів до старого run.
