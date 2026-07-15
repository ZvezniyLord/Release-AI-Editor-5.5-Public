# CODEX JOURNAL FACTORY — CYCLIC EXECUTION PLAN

## Перше завдання для агента — дуже коротко

> Клонуй `https://github.com/ZvezniyLord/Release-AI-Editor-5.5.git`.
> Перед зміною видимості перевір історію Git на секрети, токени, приватні архіви, персональні дані й великі бінарні файли. Якщо витоків немає — зроби репозиторій публічним, створи в ньому цей план і систему звітів, запуш зміни та поверни публічне посилання, commit SHA і шлях до першого звіту. Після цього зупинись.

---

## 1. Мета

Побудувати відтворюваний production-конвеєр, який отримує архів конференції зі статтями, заявками, маніфестом і шаблонами та створює журнал DOCX/PDF без втрати тексту, DOI, UDC, ORCID, таблиць, рисунків, формул, textboxes, стилів, секцій, пагінації й бізнес-логіки.

Проєкт не вважається успішним лише тому, що тести зелені. Головний доказ — відкритий DOCX/PDF, візуальний render, source-to-final audit і відсутність невідомих втрат.

---

## 2. Вихідна проблема, яку треба зафіксувати

Поточний smoke-результат демонструє, що архітектура й тести не покривають реальну редакторську роботу.

Зафіксовані регресії:

- обкладинка й службові сторінки містять змішані назви різних конференцій;
- у метаданих є заглушка `0000000 p.`;
- у різних місцях одночасно зустрічаються поточний номер конференції та старий URL;
- TOC перетворився на багатосторінкову вузьку таблицю з дублями;
- у TOC потрапляють посади, анкети й повторні фрагменти замість канонічних `section → authors → title`;
- крайні колонки таблиці займають велику ширину, а зміст стискається в середині;
- один і той самий автор або заголовок повторюється;
- production-перевірки не зупинили очевидно непридатний документ.

Ці дефекти потрібно зберегти як baseline fixture і regression evidence, а не приховувати новою генерацією.

---

## 3. Репозиторій і публічність

Цільовий репозиторій:

```text
https://github.com/ZvezniyLord/Release-AI-Editor-5.5
```

### 3.1. Перед відкриттям репозиторію

Агент зобов’язаний:

1. Перевірити власника, remote, default branch і права.
2. Створити локальний backup bundle:
   ```bash
   git bundle create ../Release-AI-Editor-5.5-before-public.bundle --all
   ```
3. Перевірити поточне дерево і всю Git-історію на:
   - API keys;
   - GitHub tokens;
   - паролі;
   - `.env`;
   - SSH/private keys;
   - credentials у URL;
   - приватні статті, заявки, анкети;
   - персональні email/телефони;
   - платні шрифти;
   - великі ZIP/DOCX/PDF з реальними матеріалами конференцій.
4. Запустити доступний secret scanner. За наявності `gitleaks`:
   ```bash
   gitleaks detect --source . --redact --no-banner
   ```
5. Додатково перевірити:
   ```bash
   git grep -nEi "(api[_-]?key|token|secret|password|passwd|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY)"
   git log --all --stat
   git rev-list --objects --all
   ```
6. Не робити репозиторій публічним, якщо секрети або приватні матеріали ще присутні в історії.
7. Якщо знайдено ризик — очистити історію окремим контрольованим кроком, перевипустити секрети й додати звіт `reports/security/PUBLIC_VISIBILITY_BLOCKED.md`.

### 3.2. Зміна видимості

Тільки після успішної перевірки:

```bash
gh repo edit ZvezniyLord/Release-AI-Editor-5.5 \
  --visibility public \
  --accept-visibility-change-consequences
```

Після зміни перевірити:

```bash
gh repo view ZvezniyLord/Release-AI-Editor-5.5 \
  --json nameWithOwner,url,visibility,defaultBranchRef
```

Не забувати: після переходу в public можуть стати доступними історія GitHub Actions і логи. Тому логи також мають бути перевірені на секрети.

---

## 4. Обов’язкова структура керування роботою

Створи в репозиторії:

```text
AGENTS.md
docs/
  CODEX_JOURNAL_FACTORY_CYCLIC_EXECUTION_PLAN.md
  BUSINESS_RULES.md
  ARCHITECTURE_DECISIONS.md
reports/
  STATUS.md
  CURRENT_CYCLE.md
  KNOWN_DEFECTS.md
  DECISION_LOG.md
  runs/
    YYYY-MM-DD_HHMM_<cycle-name>/
      SUMMARY.md
      COMMANDS.log
      TEST_RESULTS.md
      ARTIFACT_MANIFEST.json
      DEFECTS.md
      MODEL_RESPONSES.json
      CHECKSUMS.sha256
artifacts/
  README.md
fixtures/
  synthetic/
  golden/
```

### Заборона

Не комітити в public repo реальні архіви конференцій, анкети, приватні заявки або матеріали, щодо яких немає дозволу на публікацію. Для тестів використовувати synthetic fixtures або очищені golden samples.

---

## 5. Незмінний цикл роботи агента

Агент працює короткими вертикальними циклами. Один цикл має давати видимий результат.

### Крок 1 — SYNC

```bash
git fetch --all --prune
git status --short
git branch --show-current
git log -1 --oneline
```

Записати вихідний SHA у `reports/CURRENT_CYCLE.md`.

### Крок 2 — Визначити один дефект

Не брати одразу десять модулів. Обрати одну перевірювану проблему, наприклад:

- неправильна структура TOC;
- змішані метадані конференції;
- втрачений ORCID;
- дубльований службовий блок;
- втрачена таблиця;
- неправильний порядок авторів.

### Крок 3 — Створити regression fixture

До зміни production-коду створити мінімальний тестовий приклад, що відтворює дефект.

Fixture повинен мати:

- source input;
- expected semantic structure;
- expected OOXML properties;
- expected visual output або golden crop;
- явний failure code.

### Крок 4 — Написати план на один цикл

У `reports/CURRENT_CYCLE.md`:

```markdown
# Current cycle

## Defect
...

## Source evidence
...

## Expected result
...

## Files to change
...

## Tests to add
...

## Visible artifact to produce
...

## Stop condition
...
```

### Крок 5 — Внести мінімальну зміну

Не перебудовувати весь pipeline, якщо дефект виправляється локально.

Кожна зміна повинна бути:

- детермінованою;
- покритою тестом;
- fail-closed;
- відтворюваною в Docker;
- незалежною від конкретного прізвища чи номера конференції.

### Крок 6 — Запустити повні тести

Мінімум:

```bash
pytest -q
docker compose build
docker compose run --rm journal-factory pytest -q
```

Якщо тестів багато — дозволено окремий швидкий цикл, але перед push обов’язково запускати повний набір.

### Крок 7 — Створити реальний видимий артефакт

Кожен функціональний цикл повинен створити хоча б один із результатів:

- DOCX;
- PDF;
- page renders;
- contact sheet;
- source-to-final audit;
- golden comparison report.

Наявність лише JSON або unit tests недостатня.

### Крок 8 — Перевірити результат незалежно

Перевірки мають включати:

- XML/OOXML audit;
- deterministic semantic audit;
- render у PDF;
- PNG усіх сторінок;
- visual diff;
- ручний перелік видимих дефектів;
- SHA-256 артефактів.

### Крок 9 — Оновити звіти

Оновити:

- `reports/STATUS.md`;
- `reports/KNOWN_DEFECTS.md`;
- `reports/DECISION_LOG.md`;
- каталог конкретного run.

### Крок 10 — Commit і push

Один commit — один зрозумілий результат.

```bash
git add <only intended files>
git diff --cached --check
git commit -m "<imperative summary>"
git push
```

### Крок 11 — Зупинка

Після push агент повинен повернути:

- public repo URL;
- branch;
- commit SHA;
- report path;
- artifact paths;
- tests summary;
- список залишених дефектів.

Після цього він зупиняється й чекає наступного завдання. Не починає автоматично новий великий PR.

---

## 6. Джерела істини

Пріоритет:

1. Затверджений редактором golden journal.
2. Затверджений ETALON.
3. Source articles.
4. Application/manifest.
5. Детерміновані бізнес-правила.
6. LLM-підказки.

LLM ніколи не є єдиним джерелом істини для видалення, перестановки або переписування авторського матеріалу.

---

## 7. Обов’язкова бізнес-логіка

### 7.1. Службові сторінки

- Не перебудовувати `add_paragraph()` з нуля.
- Замінювати значення лише всередині затвердженої структури ETALON.
- Зберігати section breaks, headers, footers, textboxes, shapes, page numbering і relationships.
- Забороняти залишки метаданих попередньої конференції.
- Перевіряти title, dates, city, country, conference id, URL, DOI, ISBN, page count, approval date.

### 7.2. Статті

- Порядок лише з manifest/application source of truth.
- Не використовувати ZIP order.
- Не вважати кожен DOCX статтею.
- Анкети й free listeners не є статтями.
- Зіставлення статті потребує незалежного збігу автора й назви.

### 7.3. Ідентифікатори

- DOI, UDC і ORCID зберігаються source → final.
- ORCID не є контактною інформацією.
- Очищення email/phone не може видаляти ORCID.
- Втрата хоча б одного DOI або ORCID = `FAIL`.
- DOI розташовується перед UDC, якщо такий порядок встановлено стандартом.

### 7.4. Авторська шапка

- Автор, ступінь, посада, установа, місто, країна та ORCID класифікуються окремо.
- Ручні line breaks прибираються лише коли вони не мають семантичного значення.
- Не об’єднувати різних авторів.
- Не міняти порядок авторів.
- Не переносити посаду до TOC.

### 7.5. Таблиця змісту

TOC створюється лише з нормалізованого manifest, а не з сирого текстового потоку.

Канонічний запис:

```text
SECTION
AUTHORS
TITLE
```

Для затвердженого ядра 5.5:

- одна Word-таблиця;
- три фізичні колонки;
- текст тільки в центральній колонці;
- крайні колонки порожні;
- одна стаття = один фізичний рядок;
- усередині центральної клітинки:
  - перший абзац `Tab_PIP`;
  - другий абзац `Tab_Taitl`;
- секція = окремий `Tab_SEC`;
- без номерів статей і сторінок, якщо golden contract цього не містить;
- анкети, посади, установи й дублікати не потрапляють у TOC;
- golden geometry та widths беруться з `Table.docx`, а не вгадуються.

Будь-який візуально зламаний TOC повинен блокувати preview/release, навіть якщо JSON формально валідний.

### 7.6. Об’єкти

Source snapshot і final audit мають покривати:

- paragraphs;
- runs;
- tables;
- merged cells;
- images;
- media hashes;
- drawings;
- VML/DrawingML shapes;
- textboxes;
- charts;
- equations;
- numbering;
- OLE;
- section/page breaks;
- headers/footers.

Невідома втрата = `FAIL`.

---

## 8. Роль локальної LLM

LLM використовується як контрольований класифікатор і reviewer, а не як Word-редактор.

Дозволені задачі:

- класифікація фрагмента;
- визначення ролі абзацу;
- пропозиція UDC;
- виявлення неоднозначного article-file match;
- підказка щодо boundary references;
- опис видимого дефекту;
- порівняння model vs deterministic audit.

Заборонені автономні дії:

- видалення тексту;
- переписування статті;
- зміна авторів;
- видалення ORCID/DOI;
- створення довільної структури DOCX;
- production PASS без детермінованого gate.

Кожна модельна відповідь:

- тільки JSON;
- проходить JSON Schema;
- має `model`, `prompt_version`, `source_hash`, `evidence`;
- прив’язана до paragraph indices;
- має confidence;
- при розбіжності з parser отримує `MODEL_DETERMINISTIC_DISAGREEMENT`;
- не може підвищити статус до PASS.

---

## 9. Порядок відновлення проєкту

### Milestone 0 — Public repository and reporting

Результат:

- repo public;
- без секретів;
- цей MD у `docs/`;
- система звітів;
- перший commit і URL.

### Milestone 1 — Baseline freeze

Результат:

- поточний невдалий smoke збережено як evidence;
- сформовано список всіх видимих і структурних дефектів;
- жодна стара помилка не губиться.

### Milestone 2 — Golden fixtures

Результат:

- synthetic fixture;
- golden TOC;
- golden frontmatter;
- fixture з DOI/ORCID;
- fixture з таблицею/рисунком/textbox.

### Milestone 3 — TOC repair

Спочатку виправити TOC до піксельно/структурно прийнятного вигляду. Не чіпати весь журнал одночасно.

### Milestone 4 — Frontmatter metadata

Підстановка змінних у незмінну ETALON-структуру.

### Milestone 5 — Article fidelity

Source-to-final preservation для тексту й об’єктів.

### Milestone 6 — Controlled LLM

Лише після стабільного deterministic baseline.

### Milestone 7 — Journal 137 parity

Повний журнал №137 має відтворювати затверджений результат.

### Milestone 8 — Generalization

Перевірити іншу конференцію без hardcode.

---

## 10. Definition of Done для кожного циклу

Цикл завершений лише коли:

- дефект відтворюється тестом до виправлення;
- тест проходить після виправлення;
- створений реальний DOCX/PDF або render;
- source-to-final audit не показує невідомих втрат;
- звіт закомічений;
- зміни запушені;
- commit SHA надано;
- агент зупинився.

---

## 11. Формат `reports/STATUS.md`

```markdown
# Project status

## Repository
- URL:
- Visibility:
- Default branch:
- Current SHA:

## Current milestone
...

## Last completed cycle
...

## Tests
- Host:
- Docker:
- Integration:

## Latest visible artifacts
- DOCX:
- PDF:
- Contact sheet:
- Audit:

## Known blockers
...

## Known visible defects
...

## Next single task
...

## Last updated
...
```

---

## 12. Формат звіту одного запуску

```markdown
# Run summary

## Goal
...

## Input
- source:
- source hash:
- ETALON:
- ETALON hash:

## Commands
...

## Code changes
...

## Tests
...

## Output
- DOCX:
- PDF:
- pages:
- render:
- hashes:

## Source-to-final audit
- text loss:
- DOI loss:
- ORCID loss:
- UDC loss:
- table loss:
- media loss:
- textbox loss:

## Visual defects
...

## Status
PASS | REVIEW | BLOCKED | FAIL

## Stop reason
...
```

---

## 13. Точний перший prompt для Codex

```text
Працюй лише над Task 0.

1. Клонуй:
   https://github.com/ZvezniyLord/Release-AI-Editor-5.5.git

2. Перевір owner/remote/default branch і створи git bundle backup.

3. Перевір поточне дерево, Git history і доступні GitHub Actions logs на:
   secrets, tokens, passwords, private keys, .env, credentials,
   приватні статті/анкети/заявки, персональні дані, платні шрифти
   та великі приватні DOCX/PDF/ZIP.

4. Якщо існує хоча б один ризик — НЕ роби repo public.
   Створи reports/security/PUBLIC_VISIBILITY_BLOCKED.md,
   закоміть тільки безпечний звіт і повідом blocker.

5. Якщо ризиків немає:
   - зроби repo public;
   - створи docs/CODEX_JOURNAL_FACTORY_CYCLIC_EXECUTION_PLAN.md;
   - створи reports/STATUS.md;
   - створи reports/INITIAL_REPOSITORY_AUDIT.md;
   - додай AGENTS.md з вимогою працювати короткими вертикальними циклами;
   - commit і push.

6. Не змінюй journal pipeline, TOC, LLM або DOCX-код на цьому кроці.

7. Після push поверни:
   - public repo URL;
   - visibility;
   - default branch;
   - commit SHA;
   - paths до трьох звітних файлів;
   - короткий security result.

8. Після цього зупинись.
```
