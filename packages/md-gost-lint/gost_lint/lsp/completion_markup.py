"""Templates for block figures, grid tables and inline Markdown links."""

import re

from gost_lint.lsp.completion_block_templates import TEMPLATES as BLOCK_TEMPLATES
from gost_lint.lsp.completion_tables import TABLE
from gost_lint.lsp.completion_templates import Template
from gost_lint.lsp.completion_types import Suggestion
from gost_lint.markdown import Document

FIGURE = Template(
    "Рисунок",
    ("!", "![", "img", "image", "fig", "рисунок", "изображение"),
    "![${1:Название рисунка}](${2:img/figure.png}){#fig:${3:KEY}}",
    ("fig", "figure"),
)
GRID = Template(
    "Таблица с сеткой",
    ("+", "grid", "сетка"),
    "<!-- #tbl:${1:KEY} ${2:Название таблицы} -->\n\n"
    "+----------+----------+\n"
    "| Параметр | Значение |\n"
    "+==========+==========+\n"
    "| Текст    | Пример   |\n"
    "+----------+----------+",
    ("tbl", "table"),
)
LINK = Template("Ссылка", ("link", "ссылка", "["), "[${1:Текст ссылки}](${2:адрес})")
BIBLIOGRAPHY = Template(
    "Источник",
    ("bib", "источник"),
    "<!-- #bib:${1:KEY} ${2:Описание источника} -->",
    ("bib", "source"),
)
FORMULA = Template(
    "Формула",
    ("eq", "formula", "формула", "latex", "$$"),
    "<!-- #eq:${1:KEY} -->\n\n"
    r"\$\$${2:E = mc^{2\}}\$\$"
    "\n\n"
    r"где \$${3:E}\$ — ${4:пояснение}.",
    ("eq", "formula"),
)
TEMPLATES = (TABLE, FIGURE, GRID, LINK, BIBLIOGRAPHY, FORMULA, *BLOCK_TEMPLATES)
LINK_START = re.compile(r"(?<![!\\])\[$")


def _replace_end(before: str, after: str) -> int | None:
    if after.startswith("]") and before.endswith("["):
        return None if after.startswith("](") else len(before) + 1
    return None if after.strip() else len(before)


def markup_suggestions(
    document: Document,
    documents: list[Document],
    line: int,
    column: int,
    *,
    snippets: bool,
) -> list[Suggestion]:
    """Handle markup suggestions."""
    if not document.is_prose_position(line, column):
        return []
    source = document.lines[line] if line < len(document.lines) else ""
    before = source[:column]
    end = _replace_end(before, source[column:])
    if end is None:
        return []
    if LINK_START.search(before):
        return [LINK.suggest(documents, (column - 1, end), snippets=snippets)]
    prefix = before.lstrip()
    bounds = (column - len(prefix), end)
    return [
        template.suggest(documents, bounds, snippets=snippets)
        for template in TEMPLATES
        if template.matches(prefix)
    ]
