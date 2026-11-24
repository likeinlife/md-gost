"""Rules and autofix for headings that should not carry section numbers."""

import re
from collections.abc import Iterator
from typing import Final

from gost_lint.markdown import Document
from gost_lint.repairs import Repair
from gost_lint.rules.registry import rule

FileIssue = Iterator[tuple[int, int, str]]
HEADING_NUMBER_DOT = re.compile(r"^(#{1,6}\s+)(\d+(?:\.\d+)*)\.(\s+)")
HEADING_NUMBER = re.compile(r"^(?P<hashes>#{1,6}\s+)(?P<num>\d+(?:\.\d+)*\.?)\s+(?P<title>.+?)\s*$")
STRUCTURAL_TITLES: Final = frozenset(
    (
        "содержание",
        "реферат",
        "введение",
        "заключение",
        "список литературы",
        "список источников",
        "список использованных источников",
        "список использованной литературы",
        "библиографический список",
        "нормативные ссылки",
        "термины и определения",
        "обозначения и сокращения",
        "перечень сокращений и обозначений",
    ),
)
HEADING_KIND = "heading"


def structural_heading(line: str) -> re.Match[str] | None:
    """Return the heading of a structural element that carries a section number."""
    found = HEADING_NUMBER.match(line)
    if not found:
        return None
    title = found.group("title").rstrip(".").strip()
    return found if title.casefold() in STRUCTURAL_TITLES else None


@rule("STRUCT008", "error", "точка после номера раздела в заголовке")
def numbered_heading_dot(doc: Document) -> FileIssue:
    """Handle numbered heading dot."""
    for block in doc.of_kind(HEADING_KIND):
        found = HEADING_NUMBER_DOT.match(block.lines[0])
        if not found:
            continue
        number = found.group(2)
        yield (
            block.start,
            len(found.group(1)) + len(number) + 1,
            f"«{number}.» — после номера раздела точка не ставится, нужно «{number} …»",
        )


@rule("STRUCT009", "error", "номер у ненумеруемого структурного элемента")
def numbered_structural_element(doc: Document) -> FileIssue:
    """Handle numbered structural element."""
    for block in doc.of_kind(HEADING_KIND):
        found = structural_heading(block.lines[0])
        if not found:
            continue
        yield (
            block.start,
            len(found.group("hashes")) + 1,
            (
                f"«{found.group('title')}» — структурный элемент работы не нумеруется, "
                f"номер «{found.group('num')}» нужно убрать"
            ),
        )


def heading_repairs(document: Document) -> Iterator[Repair]:
    """Handle heading repairs."""
    for block in document.of_kind(HEADING_KIND):
        yield from _heading_repairs(block.start - 1, block.lines[0])


def _heading_repairs(line: int, title: str) -> Iterator[Repair]:
    found = structural_heading(title)
    if found:
        start, end = found.start("num"), found.start("title")
        yield Repair("STRUCT009", line, start, end, "", "убрать номер у заголовка")
    dot = HEADING_NUMBER_DOT.match(title)
    if dot:
        start = dot.end(2)
        yield Repair("STRUCT008", line, start, start + 1, "", "убрать точку после номера")
