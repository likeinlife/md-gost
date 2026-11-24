"""Work-level naming convention for the final section."""

import re
from collections.abc import Iterator

from gost_lint.markdown import Block, Document
from gost_lint.rules.registry import rule
from gost_lint.work import Work

WorkIssue = Iterator[tuple[Document, int, int, str]]
NUMBER_PREFIX = re.compile(r"^\s*[\d.]+\s*")
FINAL_TITLE = "Заключение"
FINAL_ALIASES = ("вывод", "выводы", "итог", "итоги", "заключительная часть")


def _title(heading: Block) -> str:
    return heading.meta.get("title", "").strip()


@rule("STRUCT007", "error", "последний раздел работы назван не «Заключение»", scope="work")
def final_section_naming(work: Work) -> WorkIssue:
    """Handle final section naming."""
    for doc in reversed(work.docs):
        section_level = 2
        headings = [heading for heading, _ in doc.main_sections() if heading.level <= section_level]
        if headings:
            yield from _check_final_title(doc, headings[-1])
            return


def _check_final_title(doc: Document, last: Block) -> WorkIssue:
    title = NUMBER_PREFIX.sub("", _title(last)).strip()
    title_lower = title.casefold()
    if title_lower == FINAL_TITLE.casefold() or title_lower not in FINAL_ALIASES:
        return
    yield (
        doc,
        last.start,
        1,
        f"последний раздел работы назван «{title}» — по ГОСТ он называется «{FINAL_TITLE}»",
    )
