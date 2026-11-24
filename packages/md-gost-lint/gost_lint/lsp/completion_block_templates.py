"""Fenced code, listing and diagram templates for the Markdown editor."""

from gost_lint.lsp.completion_templates import Template

TEMPLATES = (
    Template("Блок кода", ("code", "код"), "```${1:python}\n${2:pass}\n```"),
    Template(
        "Листинг кода",
        ("lst", "listing", "листинг"),
        '```{.${1:python} #lst:${2:KEY} caption="${3:Название листинга}"}\n${4:pass}\n```',
        ("lst", "listing"),
    ),
    Template(
        "Диаграмма PlantUML",
        ("plantuml",),
        '```{.plantuml #fig:${1:KEY} caption="${2:Последовательность запросов}"}\n'
        "${3:Клиент -> Сервис: Запрос}\n```",
        ("fig", "diagram"),
    ),
    Template(
        "График Python",
        ("plot", "график"),
        '```{.plot #fig:${1:KEY} caption="${2:Динамика показателя}"}\n'
        "${3:plt.plot([1, 2], [2, 4])}\n```",
        ("fig", "plot"),
    ),
    Template(
        "Диаграмма IDEF0",
        ("idef0",),
        '```{.idef0 #fig:${1:KEY} caption="${2:Контекстная диаграмма}"}\n'
        "context A0 : ${3:Обработать заявку}\ninput : Заявка\noutput : Результат\n"
        "control : Регламент\nmechanism : Исполнитель\n```",
        ("fig", "context"),
    ),
)
