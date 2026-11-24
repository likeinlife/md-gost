"""Rules for heading hierarchy, spelling, and duplicates."""

import re
from collections.abc import Iterator

from gost_lint.markdown import Block, Document
from gost_lint.rules.registry import rule

FileIssue = Iterator[tuple[int, int, str]]
NUMBER_PREFIX = re.compile(r"^\s*[\d.]+\s*")
TITLE_KEY = "title"
HEADING_KIND = "heading"
MAX_SHORT_TITLE = 42


def _title(heading: Block) -> str:
    return heading.meta.get(TITLE_KEY, "").strip()


def _short(heading: Block) -> str:
    title = _title(heading)
    if len(title) <= MAX_SHORT_TITLE:
        return title
    prefix = title[: MAX_SHORT_TITLE - 1]
    return f"{prefix}…"


@rule("STRUCT005", "error", "сбитая иерархия заголовков")
def heading_hierarchy(doc: Document) -> FileIssue:
    """Handle heading hierarchy."""
    previous = 0
    for block in doc.of_kind(HEADING_KIND):
        level, title = block.level, _title(block)
        if not title:
            yield (block.start, 1, "пустой заголовок")
        elif title.endswith("."):
            yield (block.start, 1, f"заголовок «{_short(block)}» кончается точкой")
        if previous and level > previous + 1:
            yield (
                block.start,
                1,
                (
                    f"уровень заголовка прыгнул с {previous} на {level} — "
                    f"пропущен промежуточный уровень"
                ),
            )
        previous = level


@rule("STRUCT006", "warning", "одинаковые заголовки в одном файле")
def duplicate_headings(doc: Document) -> FileIssue:
    """Handle duplicate headings."""
    seen: dict[str, int] = {}
    for block in doc.of_kind(HEADING_KIND):
        key = NUMBER_PREFIX.sub("", _title(block)).casefold()
        if not key:
            continue
        prior_line = seen.get(key)
        if prior_line is None:
            seen[key] = block.start
        else:
            yield (
                block.start,
                1,
                f"заголовок «{_short(block)}» повторяет заголовок строки {prior_line}",
            )
