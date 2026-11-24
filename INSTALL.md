# Установка программ

Команда `md-gost` ставится отдельно, см. [README](README.md#установка). Здесь —
Pandoc, Java, PlantUML и Graphviz. Они одинаковы для macOS и Windows. После
`winget`, `choco`, Homebrew и `setx` откройте новый терминал, чтобы подхватился
`PATH`.

Нужны Python 3.11 или новее и Pandoc 3.9.x. Java, PlantUML и Graphviz (`dot`)
нужны, только если в документе есть диаграммы. Python-зависимости (`pypandoc`,
`python-docx`, `lxml`) ставятся вместе с пакетом.

Проверка:

```bash
pandoc -v
java -version
dot -V
```

Сообщения сборки, когда программа не найдена, собраны в
[разделе «Устранение проблем»](packages/md-gost-build/README.md#устранение-проблем).

## Pandoc

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
Сборка спрашивает путь у `pypandoc.get_pandoc_path()` и находит его, даже если
каталог не добавлен в `PATH`. Команду запускайте интерпретатором, в котором
установлен pypandoc (он входит в этот пакет). Из корня репозитория, пока
глобальной команды ещё нет:

```bash
uv run --with pypandoc python -c "import pypandoc; pypandoc.download_pandoc()"
```

Та же загрузка с уже установленным пакетом:
`python -c "import pypandoc; pypandoc.download_pandoc()"`.
Чтобы взять конкретную ветку, добавьте аргумент, например `download_pandoc(version='3.9')`.

## Graphviz

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
> Для Windows может понадобиться вручную добавить `C:\Program Files\Graphviz\bin` в переменные окружения.

## PlantUML

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
