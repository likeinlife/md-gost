# md-gost

Инструмент собирает документ по ГОСТ из Markdown в файл `.docx`: рендерит
PlantUML-диаграммы, проставляет сквозную нумерацию рисунков и таблиц, собирает
список литературы и применяет стили (Times New Roman 14 pt, полуторный
интервал, поля 30/10/20/20 мм, обрамлённые таблицы).

Образец разметки — [`example/`](example/book.toml), собранный файл —
[`example/example.docx`](example/example.docx).

## Установка

Нужны Python 3.11 или новее и
[uv](https://docs.astral.sh/uv/getting-started/installation/). Из корня
репозитория:

```bash
uv tool install .
```

Команда `md-gost` после этого доступна из любого каталога. Если оболочка её
не видит, выполните `uv tool update-shell` и откройте новый терминал.
Обновление после изменений в репозитории: `uv tool install --force .`.

Графики Matplotlib и Seaborn — `uv tool install '.[plots]'`. Диагностика
в редакторе — `uv tool install '.[lsp]'` (оба сразу: `'.[lsp,plots]'`).

В своё виртуальное окружение:

```bash
uv venv
uv pip install .          # или uv pip install '.[plots]'
```

Отдельно от пакета нужны Pandoc 3.9.x и, если в документе есть диаграммы,
Java, PlantUML и Graphviz (`dot`). Пошаговая установка по ОС, переменные
`PLANTUML_JAR` и `PLANTUML`, порядок поиска — в [INSTALL.md](INSTALL.md).

Проверка:

```bash
pandoc -v
java -version
dot -V
```

Установленный пакет содержит шаблоны, сборщик, линтер и постлинтер: исходный
репозиторий для запуска не нужен. Сеть нужна при установке и обновлении
зависимостей.

Пример из любого каталога:

```bash
md-gost build /путь/к/документу
md-gost lint /путь/к/документу
```

## Сборка

Путь к каталогу с манифестом `book.toml`:

```bash
md-gost build example/
```

Готовый файл кладётся рядом с манифестом под именем из поля `output`.
Нерешённая ссылка, ошибка линтера и прочие сбои прерывают сборку с ненулевым
кодом. Шаблон стилей создаётся заново при каждом запуске.

Чтобы пропустить линтер: `md-gost build --no-lint example/`.

## Свой документ

1. Каталог, например `docs/report/`.
2. Текст в Markdown и `book.toml`.
3. `md-gost build docs/report/`.

```toml
output = "report.docx"   # по умолчанию output.docx
toc = false              # оглавление «Содержание»; по умолчанию true

chapters = [             # обязательное поле, порядок = порядок в документе
  "chapter.md",
]
```

`chapters` — единственное обязательное поле. Порядок глав задаётся списком,
файлы вне списка в сборку не входят. `toc = false` уместно для одной главы;
образец многоглавного отчёта — `example/book.toml`. Таблица `[frame]` включает
рамку ГОСТ; поля — в
[README сборщика](packages/md-gost-build/README.md#рамка-гост-основная-надпись).

За образец разметки берите [`example/`](example/).

## Проверка текста

```bash
md-gost lint example/             # документ, каталог или один файл .md
md-gost format example/
md-gost postlint путь/к/файлу.docx
```

Ошибки прерывают сборку, предупреждения печатаются. Уровни правил задаёт
`mdlint.toml`: корневой файл — общее, файл рядом с `book.toml` переопределяет
его для этого каталога. Перечень правил — в
[README линтера](packages/md-gost-lint/README.md).

## Редактор

Редактор запускает `md-gost lsp` по stdio. Нужен пакет с экстра `lsp`.
Zed — [README расширения](editors/zed/README.md).
VS Code и Cursor — [README расширения](editors/vscode/README.md).

## Дальше

- [Синтаксис разметки](packages/md-gost-build/README.md)
- [Правила текста](.claude/skills/gost-doc/SKILL.md)
- [Правила диаграмм IDEF0](.claude/skills/idef0/SKILL.md)
- [Линтер](packages/md-gost-lint/README.md)
- [Постлинтер](packages/md-gost-postlint/README.md)
- [Команда `md-gost`](packages/md-gost/README.md)
- [Диаграммы IDEF0](packages/idef0/README.md)
- [Разработка](CONTRIBUTING.md)
