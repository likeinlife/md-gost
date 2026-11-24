"""Build completion edits for GOST-captioned pipe tables."""

from gost_lint.lsp.completion_templates import Template, template_text
from gost_lint.lsp.completion_types import Suggestion
from gost_lint.markdown import Document

TABLE = Template(
    "Таблица",
    ("tbl", "table", "таблица", "|"),
    "<!-- #tbl:${1:KEY} ${2:Название таблицы} -->\n\n"
    "| ${3:Параметр} | ${4:Значение} |\n"
    "| --- | --- |\n"
    "| ${5:Параметр} | ${6:Значение} |",
    ("tbl", "table"),
)


def row_suggestion(
    document: Document,
    line: int,
    source: str,
    *,
    snippets: bool,
) -> Suggestion | None:
    """Handle row suggestion."""
    for block in document.of_kind("table"):
        if block.start <= line <= block.end and "rows" in block.meta:
            width = len(block.meta["rows"][0])
            cells = (f"${{{index}:Значение}}" for index in range(1, width + 1))
            row = "| {cells} |".format(cells=" | ".join(cells))
            return _suggest(
                "Строка таблицы",
                f"Столбцов — {width}",
                row,
                source,
                snippets=snippets,
            )
    return None


def _suggest(
    label: str,
    detail: str,
    template: str,
    source: str,
    *,
    snippets: bool,
) -> Suggestion:
    text = template_text(template, snippets=snippets)
    typed = source.strip() or None
    return Suggestion(label, detail, text, 0, len(source), snippets, typed)
