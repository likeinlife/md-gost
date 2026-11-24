# md-gost

Единственная команда. Она импортирует сервисы соседних пакетов и не разбирает их аргументы:

| Подкоманда | Вызов |
|------------|--------|
| `lint` | `gost_lint.cli.run_lint` |
| `format` | `gost_lint.format_run.Session` |
| `lsp` | `gost_lint.lsp.cli.main` |
| `build` | `gost_builder.pipeline.build` |
| `postlint` | `gost_docx_lint.check` |

```bash
md-gost lint путь/к/работе
md-gost lint --fix путь/к/работе
md-gost format путь/к/работе
md-gost build путь/к/работе
md-gost build --no-lint путь/к/работе
md-gost postlint путь/к/файлу.docx
md-gost lsp
```
