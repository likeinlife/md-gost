# md-gost

Инструмент собирает документ по ГОСТ из Markdown в файл `.docx`. Исходники
пишутся обычным текстом, команда `md-gost` вызывает сборщик
[`packages/md-gost-build`](packages/md-gost-build/README.md): рендерит
PlantUML-диаграммы, проставляет сквозную нумерацию рисунков и таблиц, собирает
список литературы и применяет стили (Times New Roman 14 pt, полуторный
интервал, поля 30/10/20/20 мм, обрамлённые таблицы).

Готовый образец всех приёмов оформления лежит в [`example/`](example/book.toml).
Собранный файл — `example/example.docx`.

## Состав репозитория

| Путь | Назначение |
|------|------------|
| `packages/md-gost/` | Команда `md-gost`: lint, format, build, postlint, lsp |
| `packages/md-gost-build/` | Сборщик Markdown → ГОСТ `.docx` и тесты |
| `packages/md-gost-lint/` | Линтер исходных `.md`: структура разделов, ссылки, оформление текста |
| `packages/md-gost-postlint/` | Проверка OOXML готового `.docx` |
| `packages/idef0/` | Диаграммы IDEF0: текст в Markdown и отрисовка из Python |
| `example/` | Демонстрационный документ со своим `book.toml` |
| `editors/zed/`, `editors/vscode/` | Расширения редактора поверх `md-gost lsp` |
| `.claude/skills/gost-doc/` | Правила написания текста, которые сборка не проверяет |
| `AGENTS.md` | Правила для ИИ-агентов, которые правят этот репозиторий |

Рабочие каталоги сборки (`.md-to-gost/`, `.venv/`) добавлены в `.gitignore`.

## Требования

Нужны Python 3.11 или новее, Pandoc 3.9.x и, если в документе есть диаграммы,
Java, PlantUML и Graphviz (`dot`). Python и пакет ставятся в следующем разделе.
Остальное ставится отдельно, одинаково для macOS и Windows: после установки
откройте новый терминал, чтобы подхватился `PATH`.

Проверка:

```bash
pandoc -v
java -version
dot -V
```

### Pandoc

Страница установки: <https://pandoc.org/installing.html>. Сборка рассчитана на 3.9.x.

macOS:

```bash
brew install pandoc
```

Windows:

```powershell
winget install --source winget --exact --id JohnMacFarlane.Pandoc
```

Второй способ — скачать Pandoc через pypandoc. По умолчанию файл кладётся в
`%LOCALAPPDATA%\Pandoc` на Windows и в `~/Applications/pandoc` на macOS.
`md-gost build` находит его сам, даже если каталог не добавлен в `PATH`.
Команду запускайте интерпретатором, в котором установлен pypandoc
(он входит в этот пакет). Из корня репозитория, пока глобальной команды ещё нет:

```bash
uv run --with pypandoc python -c "import pypandoc; pypandoc.download_pandoc()"
```

Та же загрузка с уже установленным пакетом: `python -c "import pypandoc; pypandoc.download_pandoc()"`.
Чтобы взять конкретную ветку, добавьте аргумент, например `download_pandoc(version='3.9')`.

### Graphviz

PlantUML вызывает `dot` для диаграмм, которые не раскладывает сам (классы,
компоненты, развёртывание и часть остальных). Диаграммы последовательности
обычно строятся и без Graphviz. Если `dot` нет в `PATH`, сборка печатает
предупреждение и идёт дальше.

macOS:

```bash
brew install graphviz
```

Windows — страница загрузки <https://graphviz.org/download/> приводит `winget`.
Подойдёт любая из команд:

```powershell
winget install graphviz
winget install --source winget --exact --id Graphviz.Graphviz
choco install graphviz
```

Если после нового терминала `dot -V` не находится, добавьте в `PATH` каталог
`bin` установленного Graphviz.

> [!NOTE]
> Для Windows может понадобиться вручную добавить "C:\Program Files\Graphviz\bin" в Переменные окружения

### PlantUML

Проект: <https://github.com/plantuml/plantuml>.
Релиз, под который написана эта инструкция:
<https://github.com/plantuml/plantuml/releases/tag/v1.2026.10>.

macOS, команда `plantuml` в `PATH` (формула Homebrew ставит и Java):

```bash
brew install plantuml
plantuml -version
```

Windows и установка одним jar на любой системе. Скачайте из релиза файл
`plantuml.jar` (тот же архив, что `plantuml-1.2026.10.jar`) и положите его
в каталог, например `K:\user\Apps\Plantuml\plantuml.jar`. Для этого jar нужна
Java 17 или новее. В том же релизе есть `plantuml-java8-1.2026.10.jar` — сборка
для Java 8; её подключают переменной `PLANTUML_JAR`, если новый JDK ставить нельзя.

Java на Windows:

```powershell
winget install --source winget --exact --id EclipseAdoptium.Temurin.21.JDK
```

Java на macOS, если не пользуетесь формулой `plantuml`:

```bash
brew install --cask temurin
```

Сборка ищет PlantUML в таком порядке и берёт первое совпадение:

1. `PLANTUML_JAR` — полный путь к jar, имя файла любое.
2. `PLANTUML` — полный путь к программе (`plantuml`, `plantuml.exe`, нативный
   исполняемый файл) или к jar.
3. Команда `plantuml` в `PATH`: скрипт Homebrew на macOS, `plantuml.exe` на Windows.
4. Файл с именем `plantuml.jar` в любом каталоге из `PATH`.
5. Если в `PATH` нашёлся `plantuml.bat` или `plantuml.cmd`, рядом с ним ищется
   `plantuml.jar`.

На Windows `shutil.which("plantuml")` перебирает только расширения из `PATHEXT`
(`.exe`, `.bat`, `.cmd` и другие) и jar не видит. Каталог с одним jar либо
добавьте в `PATH` (шаг 4), либо укажите файл через `PLANTUML_JAR`. Pandoc не
запускает `.bat` и `.cmd`: если рядом с обёрткой лежит `plantuml.jar`, сборка
вызывает `java -jar`. Версионное имя `plantuml-1.2026.10.jar` само по `PATH`
не находится — переименуйте файл в `plantuml.jar` или задайте `PLANTUML_JAR`.

Постоянная переменная на Windows (её подхватывает новый терминал):

```powershell
setx PLANTUML_JAR "K:\user\Apps\Plantuml\plantuml.jar"
```

Либо добавьте `K:\user\Apps\Plantuml` в пользовательский `PATH` и оставьте
имя файла `plantuml.jar`. Проверка:

```powershell
java -jar K:\user\Apps\Plantuml\plantuml.jar -version
```

На macOS тот же приём:

```bash
export PLANTUML_JAR="$HOME/Apps/plantuml.jar"
```

Чтобы обойтись без Java, в релизе есть нативный исполняемый файл:
`native-plantuml-windows-amd64-1.2026.10.zip` и
`native-plantuml-macos-arm64-1.2026.10.zip`. Распакуйте архив и укажите
`PLANTUML` на этот файл либо положите его в `PATH` под именем `plantuml.exe`
(Windows) или `plantuml` (macOS).

Порядок поиска и сообщения об ошибках также описаны в
[README сборщика](packages/md-gost-build/README.md#требования).

## Установка команд

Установите [uv](https://docs.astral.sh/uv/getting-started/installation/) и из корня
клонированного репозитория выполните:

```bash
uv tool install .
```

После этого команда `md-gost` доступна из любого каталога. Если она не
находится, выполните `uv tool update-shell` и
перезапустите терминал. Для графиков установите пакет с дополнительными зависимостями:
`uv tool install '.[plots]'`. Для обновления после изменений в репозитории используйте
`uv tool install --force .` (или `--force '.[plots]'`).

Вместо отдельного инструмента пакет можно установить в своё виртуальное окружение:

```bash
uv venv
uv pip install .          # или uv pip install '.[plots]'
source .venv/bin/activate
```

Пример из любого каталога:

```bash
md-gost build /путь/к/документу
md-gost lint /путь/к/документу
```

Pandoc, PlantUML, Java и Graphviz устанавливаются отдельно, как указано выше.
PlantUML и Java нужны только для документов с диаграммами, Graphviz — для тех
диаграмм, которые PlantUML не раскладывает сам. Установленный пакет содержит
шаблоны, сборщик, линтер и постлинтер; исходный репозиторий после установки
для запуска не требуется. Для
установки и обновления Python-зависимостей нужен доступ к индексу пакетов или
заполненный кэш uv.

## Работа в редакторе

Для диагностики при наборе, подсказок по таблицам и переходов по ссылкам установите
пакет из корня репозитория командой `uv tool install '.[lsp]'`. Чтобы также строить
графики, выберите `'.[lsp,plots]'`. Редактор запускает `md-gost lsp` по stdio.
Инструкцию для Zed и проверку на каталоге `example/` см. в [README расширения](editors/zed/README.md).
Для VS Code и Cursor — в [README расширения](editors/vscode/README.md).

## Сборка

Одна команда на каждый документ — путь к каталогу с манифестом `book.toml`:

```bash
md-gost build example/
```

Готовый файл кладётся рядом с манифестом под именем из поля `output`. Любая
ошибка — включая нерешённую перекрёстную ссылку — прерывает сборку с ненулевым
кодом возврата. Сборка идемпотентна: шаблон стилей `reference.docx` создаётся
заново каждый запуск, поэтому устаревшие стили не накапливаются.

## Проверка текста

Перед сборкой исходники проверяет линтер [`packages/md-gost-lint`](packages/md-gost-lint/README.md):

```bash
md-gost lint                      # весь репозиторий
md-gost lint example/             # один документ или отдельный файл
md-gost format example/
md-gost postlint путь/к/файлу.docx
```

Он ловит то, чего сборка не видит: раздел, оканчивающийся таблицей вместо вывода;
жирный шрифт в основном тексте; набранный руками номер рисунка; ссылку `[@bib:…]`
не на своём месте. Ошибки прерывают сборку, предупреждения только печатаются.
Обойти проверку — `md-gost build --no-lint <каталог>`.

Python-код инструментов дополнительно проверяет wemake-python-styleguide через
pre-commit. Запустить проверки вручную для всех файлов:

```bash
pre-commit run --all-files
```

Конфигурация WPS находится в `packages/md-gost/setup.cfg`,
`packages/md-gost-lint/setup.cfg` и `packages/md-gost-build/setup.cfg`; хуки
устанавливают плагин автоматически.

Уровни правил задаются в `mdlint.toml`: корневой файл держит общие настройки, а
документ может положить свой рядом с `book.toml` — он переопределяет корневой и
действует только на этот каталог. Так короткому документу можно отключить правило
о списке в конце раздела, если перечень вместо развёрнутого заключения там уместен.

## Манифест `book.toml`

Каждый собираемый документ описывается манифестом в своём каталоге:

```toml
output = "report.docx"   # имя выходного файла, по умолчанию output.docx
toc = false              # оглавление «Содержание»; по умолчанию true

chapters = [             # обязательное поле, порядок = порядок в документе
  "chapter.md",
]
```

- `chapters` — единственное обязательное поле. Порядок глав задаётся здесь, а не
  структурой каталогов; файлы, не попавшие в список, в сборку не включаются.
- `toc = false` уместно для документа из одной главы, `true` (значение по умолчанию) —
  для многоглавного отчёта. Образец второго случая — `example/book.toml`.
- Таблица `[frame]` включает рамку ГОСТ с основной надписью; подробности — в
  [README инструмента](packages/md-gost-build/README.md#рамка-гост-основная-надпись).

## Как собрать свой документ

1. Создать каталог, например `docs/report/`.
2. Положить туда текст в Markdown и манифест `book.toml` с полями `chapters` и `output`.
3. Собрать: `md-gost build docs/report/`.

За образец разметки берите [`example/`](example/).

## Документация

- [`packages/md-gost/README.md`](packages/md-gost/README.md) — какая подкоманда какой
  модуль вызывает.
- [`packages/md-gost-postlint/README.md`](packages/md-gost-postlint/README.md) — проверки
  готового `.docx`.
- [`packages/md-gost-build/README.md`](packages/md-gost-build/README.md) — полный справочник по
  синтаксису: диаграммы, таблицы, перекрёстные ссылки `[@fig:…]` / `[@tbl:…]`,
  библиография `[@bib:…]`, растровые изображения, доступные стили Word. Описывает
  контракт инструмента: всё, нарушение чего прерывает сборку.
- [`.claude/skills/gost-doc/SKILL.md`](.claude/skills/gost-doc/SKILL.md) — правила
  написания текста, которые сборка проверить не может: раздел не сводится к одной
  таблице и не кончается ею, жирный шрифт только в заголовках, ссылка вписывается
  в предложение, `[@bib:…]` — перед точкой в конце.
- [`packages/md-gost-lint/README.md`](packages/md-gost-lint/README.md) — перечень правил линтера,
  их уровни и настройка через `mdlint.toml`.
- [Диаграммы IDEF0](packages/idef0/README.md) — текстовый формат для Markdown,
  описание моделей в Python и оформление для печати.
- [`AGENTS.md`](AGENTS.md) — правила для ИИ-агентов, работающих с репозиторием.
- [`example/`](example/) — рабочий пример всех приёмов оформления сразу.
