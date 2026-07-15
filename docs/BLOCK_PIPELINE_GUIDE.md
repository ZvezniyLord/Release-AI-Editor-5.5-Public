# Блочна Оркестрація Нормалізації

Оновлено: 2026-03-23

## Мета
- Перейти від монолітної обробки до схеми `detector -> handlers`.
- Зібрати ключові блоки статті в одному проході й обробляти їх окремими модулями.
- Прибрати дублювання кроків у GUI: розбір шапки виконується всередині кроку нормалізації.

## Поточна реалізація

### 1) Detector
- `core/block_detector.py`
- Визначає блоки: `UDC`, `header`, `title`, `annotation`, `keywords`, `references`.
- Записує карту блоків у `Статті_норм/logs/<file>.blocks.json`.

### 2) Handlers
- `core/block_handlers/markers_block.py`
- Викликає `apply_markers(...)` для нормалізації:
  - annotation;
  - keywords;
  - references.

- `core/block_handlers/header_block.py`
- Запускає `shapka_core/shapka_main.py` для папки `Статті_норм`.
- Формує `run_dir/shapka_report.json`.

### 3) Orchestrator
- `core/block_pipeline.py`
- Порядок:
  1. detect blocks;
  2. write block report;
  3. run markers handler.

## Інтеграція у pipeline
- `core/normalize_pipeline.py`:
  - робить `normalize_docx(...)`;
  - викликає `process_article_blocks(...)`;
  - пише прогрес `"[normalize] i/total"` для GUI.

- `core/normalize_main.py`:
  - після нормалізації й title-етапу запускає header-block (`shapka`) автоматично;
  - доданий прапор `--skip-header-block`.

## GUI
- `launcher.py`
- Кнопка `4. Розібрати шапку` прибрана.
- Крок `3. Нормалізувати статті (всі блоки)` тепер включає:
  - базову нормалізацію;
  - block detection;
  - markers block;
  - header block (shapka).

## Чому це правильний варіант
- Точка входу одна: крок 3.
- Логіка розділена на модулі з чіткою відповідальністю.
- Зміни в правилах конкретного блоку не потребують переписування всього пайплайну.
- Є діагностика по блоках через `.blocks.json`.

## Порядок Верхніх Блоків
- Джерело істини для назви: `matches.json` (`item.title`), без евристик по References.
- Після етапу `normalize_titles` виконується примусове впорядкування у `normalize_main.py`:
  1. `УДК`
  2. `шапка`
  3. `назва`
- Реалізація: `core/block_handlers/order_block.py`.

## Політика Кодування
- Усі source-файли мають бути UTF-8.
- Кириличні службові заголовки в коді задаються коректними Unicode-літералами.
- Для раніше зіпсованих префіксів маркерів (`РљР...`, `РђР...`) в нормалізаторі є точкове виправлення префікса перед матчингом.
