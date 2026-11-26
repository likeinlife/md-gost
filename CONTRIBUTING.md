# Разработка

Как менять сам инструмент. Сборка своего документа описана в
[README](README.md). Правила для ИИ-агентов — в [AGENTS.md](AGENTS.md).

## Состав репозитория

| Путь | Назначение |
|------|------------|
| `packages/md-gost/` | Команда `md-gost`: lint, format, build, postlint, lsp |
| `packages/md-gost-build/` | Сборщик Markdown → ГОСТ `.docx` и тесты |
| `packages/md-gost-lint/` | Линтер исходных `.md` |
| `packages/md-gost-postlint/` | Проверка OOXML готового `.docx` |
| `packages/idef0/` | Диаграммы IDEF0 |
| `example/` | Демонстрационный документ со своим `book.toml` |
| `editors/zed/`, `editors/vscode/` | Расширения редактора поверх `md-gost lsp` |
| `.claude/skills/gost-doc/` | Правила текста, которые сборка не проверяет |
| `.claude/skills/idef0/` | Правила диаграмм IDEF0 в главах |

У `packages/md-gost-postlint/` своего манифеста нет: его подключает корневой
`pyproject.toml`. У остальных пакетов свой `pyproject.toml`, и настройки Ruff,
Pyrefly и pytest живут там. Рабочие каталоги `.md-to-gost/` и `.venv/`
добавлены в `.gitignore`.

## Проверки

Ruff и wemake-python-styleguide запускает корневой pre-commit:

```bash
pre-commit run --all-files
```

Конфигурация WPS — `setup.cfg` в `packages/md-gost/`, `packages/md-gost-lint/`
и `packages/md-gost-build/`. Pyrefly в pre-commit не входит. Из каталога
пакета, который меняли:

```bash
uvx pyrefly check
```

У сборщика те же проверки расписаны в его
[README](packages/md-gost-build/README.md#проверки-кода).

## Тесты

```bash
cd packages/md-gost && uv run --group dev pytest
cd packages/md-gost-build && uv run --group dev --extra plots pytest
cd packages/md-gost-lint && uv run --group dev pytest
```

Золотой тест сборщика сверяет `example/`. После правки исходников этого
документа пересоберите `example/example.docx` и коммитьте его вместе с ними.
Кеш `.md-to-gost/` в коммит не входит.
