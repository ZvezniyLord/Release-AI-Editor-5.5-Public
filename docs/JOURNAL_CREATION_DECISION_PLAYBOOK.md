# JOURNAL CREATION DECISION PLAYBOOK

## Навіщо цей документ

Це не прихований внутрішній «ланцюжок думок» моделі. Це відтворюваний спосіб прийняття рішень під час складання наукового журналу: які дані перевіряти, які питання ставити, які докази збирати, коли зупиняти pipeline і як доводити, що результат правильний.

Новий працівник або Codex-агент повинен діяти за цим документом на кожному циклі.

---

## 1. Головний принцип

Журнал не «генерується». Він **збирається з доказів**.

Для кожного елемента фінального документа має бути відповідь на п’ять питань:

1. Звідки цей елемент узявся?
2. Чому він класифікований саме так?
3. Яке правило дозволило його змінити?
4. Як перевірено, що нічого не втрачено?
5. Який артефакт або audit підтверджує результат?

Якщо хоча б на одне питання немає відповіді, статус не може бути `PASS`.

---

## 2. Як мислити на вході

### 2.1. Спочатку не відкривати Word вручну, а інвентаризувати пакет

Перевірити:

- ZIP чи директорія;
- список усіх файлів;
- SHA-256 кожного файла;
- розширення;
- Office temp files;
- анкети;
- заявки;
- статті;
- шаблони;
- manifest;
- cover;
- додаткові каталоги.

Результат:

```text
archive_inventory.json
```

### 2.2. Не вважати назву файла доказом

Filename — лише слабкий сигнал.

Стаття вважається зіставленою лише коли є незалежні докази:

- автор у заявці збігається з автором у статті;
- назва в заявці збігається з назвою у статті.

Якщо збіг лише один:

```text
REVIEW
```

Якщо один source file підходить до кількох заявок:

```text
BLOCKED: AMBIGUOUS_ARTICLE_MATCH
```

### 2.3. Порядок статей

Порядок береться лише з manifest або заявки.

Заборонено:

- ZIP order;
- filesystem order;
- alphabetical order;
- порядок, у якому файли повернула бібліотека.

---

## 3. Як читати DOCX

### 3.1. Не обмежуватися `document.paragraphs`

Потрібно читати OOXML:

```text
word/document.xml
word/styles.xml
word/numbering.xml
word/_rels/document.xml.rels
word/media/*
word/charts/*
word/embeddings/*
headers
footers
textboxes
VML
DrawingML
equations
tables
```

### 3.2. Створити source snapshot до будь-яких змін

Для кожної статті зберігати:

- усі абзаци;
- усі runs;
- порядок;
- стилі;
- таблиці;
- текст клітинок;
- merged cells;
- images;
- media hashes;
- textboxes;
- shapes;
- charts;
- equations;
- OLE;
- page breaks;
- section breaks;
- headers/footers;
- DOI;
- UDC;
- ORCID;
- references.

Результат:

```text
snapshots/<article_id>/source_snapshot.json
```

### 3.3. Ключове рішення

Перед зміною кожного фрагмента визначити:

```text
PRESERVE
NORMALIZE
MOVE
REMOVE
REVIEW
```

`REMOVE` дозволено лише коли:

- існує точне бізнес-правило;
- фрагмент ідентифіковано однозначно;
- audit записує, що видалено;
- видалення не зачіпає DOI, UDC, ORCID, автора, title, таблицю, рисунок або reference.

---

## 4. Як класифікувати структуру статті

Очікувані ролі:

```text
DOI
UDC
AUTHOR
DEGREE
POSITION
AFFILIATION
CITY_COUNTRY
ORCID
TITLE
ANNOTATION
KEYWORDS
BODY
TABLE
FIGURE
CAPTION
REFERENCES_TITLE
REFERENCE_ITEM
```

### 4.1. Не покладатися лише на стиль

Стиль — сильний доказ, але не абсолютний.

Потрібно враховувати:

- style ID;
- outline level;
- позицію;
- текстовий marker;
- сусідні абзаци;
- форматування;
- manifest;
- LLM classification;
- deterministic parser.

### 4.2. Конфлікт доказів

Приклад:

- стиль каже `AUTOR`;
- текст виглядає як посада;
- LLM каже `AFFILIATION`.

Тоді:

```text
MODEL_DETERMINISTIC_DISAGREEMENT
needs_operator_review
```

Не можна мовчки вибрати один варіант.

---

## 5. Як працювати з DOI, UDC і ORCID

### DOI

- зберігати дослівно;
- audit source → final;
- не перетворювати на title;
- не видаляти під час очищення контактів.

### UDC

- literal UDC має пріоритет;
- якщо відсутній — LLM може запропонувати;
- LLM-proposal не вставляється без review;
- один article = один UDC;
- дубль або кілька UDC = blocker/review.

### ORCID

ORCID — науковий ідентифікатор, не контакт.

Заборонено видаляти ORCID разом із:

- email;
- phone;
- Telegram;
- affiliation cleanup.

Втрата хоча б одного ORCID:

```text
FAIL: REQUIRED_IDENTIFIER_LOST
```

---

## 6. Як працювати з авторською шапкою

Питання для кожного рядка:

1. Це окремий автор чи продовження попереднього?
2. Це ступінь, посада чи установа?
3. Це semantic line break чи старий ручний перенос?
4. До якого автора належить ORCID?
5. Чи збігається порядок авторів із manifest/source?

### Дозволено

- прибрати зайвий manual line break;
- об’єднати рядки однієї установи;
- застосувати канонічний стиль;
- вирівняти абзац.

### Заборонено

- об’єднати двох авторів;
- переставити авторів;
- приписати ORCID іншому автору;
- видалити ступінь або установу без правила;
- переносити посади в TOC.

---

## 7. Як збирати ETALON

ETALON — не «джерело тексту», а джерело структури.

Не перебудовувати службові сторінки з нуля.

Дозволено:

- заміна placeholders;
- оновлення conference variables;
- вставлення article content у structural slot;
- оновлення TOC;
- оновлення page count після render.

Не дозволено:

- знищувати textboxes;
- дублювати institutional header;
- переносити editor block;
- ламати section breaks;
- змішувати metadata різних конференцій;
- залишати старий conference URL.

Перевірити всі змінні:

```text
conference_number
conference_title
date
city
country
approval_date
URL
ISBN
DOI
UDC
page_count
editor
publisher
```

---

## 8. Як будувати TOC

TOC не читає «весь текст документа».

TOC отримує тільки нормалізований semantic manifest:

```text
SECTION
AUTHORS
TITLE
FREE_LISTENERS
```

Для ядра 5.5:

- одна Word-таблиця;
- три фізичні колонки;
- крайні колонки порожні;
- текст у центральній;
- одна стаття = один row;
- у row два paragraphs:
  - `Tab_PIP`;
  - `Tab_Taitl`;
- section = `Tab_SEC`;
- без посад;
- без установ;
- без анкет;
- без дублювань;
- без випадкових заголовків службових сторінок.

Перед PASS:

- OOXML audit;
- width audit;
- style audit;
- row audit;
- render;
- visual comparison.

---

## 9. Як використовувати LLM

LLM не повинна «робити журнал».

LLM допомагає там, де deterministic logic не впевнена.

### Вхід LLM

- article_id;
- source hash;
- paragraph indices;
- exact excerpts;
- expected labels;
- business rules;
- JSON Schema.

### Вихід

Тільки JSON:

```json
{
  "decision_type": "fragment_classification",
  "article_id": "A001",
  "source_hash": "...",
  "status": "needs_operator_review",
  "blocks": [],
  "problems": [],
  "evidence": [],
  "confidence": 0.74,
  "model": "...",
  "prompt_version": "..."
}
```

### LLM не може

- видалити текст;
- змінити автора;
- видалити ORCID;
- дати production PASS;
- змінити DOCX напряму;
- приховати invalid JSON.

---

## 10. Як перевіряти source → final

Для кожної статті створити таблицю:

```text
metric              source   final   status
paragraphs
visible_text
tables
table_cells
images
media_hashes
textboxes
DOI
UDC
ORCID
references
authors
title
```

Окремі списки:

```text
deleted_text
inserted_text
replaced_text
lost_objects
missing_identifiers
```

### Правило

Невідоме видалення тексту:

```text
FAIL: SOURCE_TEXT_LOSS
```

Невідома втрата об’єкта:

```text
FAIL: SOURCE_OBJECT_LOSS
```

---

## 11. Як оцінювати PDF

DOCX без render не перевірений.

Обов’язково:

1. DOCX → PDF.
2. PDF → PNG кожної сторінки.
3. Contact sheet.
4. Перевірити:
   - cover;
   - frontmatter;
   - TOC;
   - start of every article;
   - tables;
   - figures;
   - captions;
   - references;
   - page numbers;
   - blank pages;
   - overflow;
   - narrow columns;
   - duplicate blocks.

---

## 12. Формат аудованого рішення

Не писати: «я подумав, що так краще».

Писати:

```markdown
## Decision D-014

### Problem
TOC contains positions and duplicated titles.

### Evidence
- outline_parser maps generic Title to level 1;
- style AUTOR is not mapped explicitly;
- rendered TOC spans 5 pages;
- rows contain application form text.

### Options
1. Keep current outline fallback.
2. Parse only canonical journal styles.
3. Generate TOC from manifest only.

### Decision
Use canonical styles and normalized manifest; reject incomplete triples.

### Why
Filename/text heuristics are insufficient and already produced false rows.

### Verification
- synthetic fixture;
- unit test;
- OOXML audit;
- PDF render;
- contact sheet;
- golden comparison.

### Status
REVIEW until visual approval.
```

Це і є відтворюваний «хід думок»: проблема → докази → варіанти → рішення → перевірка.

---

## 13. Цикл одного journal build

```text
1. BACKUP
2. INVENTORY
3. HASH
4. MATCH
5. SNAPSHOT
6. CLASSIFY
7. NORMALIZE
8. BUILD IN ETALON
9. BUILD TOC
10. RENDER
11. SOURCE-TO-FINAL AUDIT
12. VISUAL AUDIT
13. REPORT
14. STOP FOR REVIEW
```

На кожному кроці є gate.

---

## 14. Що агент зобов’язаний писати в репозиторій

Після кожного циклу:

```text
reports/CURRENT_CYCLE.md
reports/DECISION_LOG.md
reports/KNOWN_DEFECTS.md
reports/runs/<run>/SUMMARY.md
reports/runs/<run>/COMMANDS.log
reports/runs/<run>/TEST_RESULTS.md
reports/runs/<run>/ARTIFACT_MANIFEST.json
```

У `DECISION_LOG.md` записувати не приватні внутрішні міркування, а аудовані рішення за шаблоном із розділу 12.

---

## 15. Критерій успіху

Успіх — не кількість коду й не кількість тестів.

Успіх означає:

- журнал відкривається без repair warning;
- ETALON не зруйнований;
- TOC правильний;
- немає змішаних conference metadata;
- усі статті на місці;
- DOI/UDC/ORCID не втрачені;
- таблиці й рисунки збережені;
- unknown text loss = 0;
- unknown object loss = 0;
- PDF візуально прийнятний;
- є звіт, який доводить кожен результат.
