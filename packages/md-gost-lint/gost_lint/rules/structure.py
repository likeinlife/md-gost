"""Section structure: the rules a build cannot see.

A document that builds cleanly can still put a table where a conclusion
belongs. These rules read the block stream of every section — from a
heading to the next heading of any level, or to end of file.
"""

from collections.abc import Iterator
from itertools import pairwise
from types import MappingProxyType

from gost_lint.markdown import Block, Document
from gost_lint.markdown.syntax import ATTACHMENT
from gost_lint.rules.registry import rule

FileIssue = Iterator[tuple[int, int, str]]

IGNORED = ("comment",)  # invisible in the output, carries no meaning
NOISE = (*IGNORED, "table_marker", "eq_marker")
MAX_SHORT_TITLE = 42
ATTACHMENT_NAME = MappingProxyType(
    {
        "table": "таблицей",
        "diagram": "рисунком",
        "image": "рисунком",
        "formula": "формулой",
        "listing": "листингом",
    },
)


def _short(heading: Block) -> str:
    title = heading.meta.get("title", "").strip()
    if len(title) <= MAX_SHORT_TITLE:
        return title
    prefix = title[: MAX_SHORT_TITLE - 1]
    return f"{prefix}…"


def _meaningful(body: list[Block]) -> list[Block]:
    return [block for block in body if block.kind not in IGNORED]


def _attachment_message(heading: Block, attachment: Block) -> str:
    short_title = _short(heading)
    attachment_name = ATTACHMENT_NAME[attachment.kind]
    return (
        f"раздел «{short_title}» заканчивается {attachment_name} — добавьте после неё "
        "хотя бы одно предложение с выводом"
    )


@rule("STRUCT001", "error", "раздел заканчивается таблицей или рисунком вместо текстового вывода")
def ends_with_attachment(doc: Document) -> FileIssue:
    """Handle ends with attachment."""
    if doc.is_bibliography():
        return
    for heading, body in doc.main_sections():
        blocks = _meaningful(body)
        if not blocks:
            continue
        last = blocks[-1]
        if last.kind in ATTACHMENT:
            yield (
                last.start,
                1,
                _attachment_message(heading, last),
            )


@rule("STRUCT002", "warning", "раздел заканчивается списком")
def ends_with_list(doc: Document) -> FileIssue:
    """Handle ends with list."""
    if doc.is_bibliography():
        return
    for heading, body in doc.sections():
        blocks = _meaningful(body)
        if blocks and blocks[-1].kind == "list":
            yield (
                blocks[-1].start,
                1,
                (
                    f"раздел «{_short(heading)}» заканчивается списком — "
                    f"перечисление лучше закрыть связным абзацем"
                ),
            )


@rule("STRUCT003", "error", "в разделе нет ни одного абзаца — только вложения")
def no_prose(doc: Document) -> FileIssue:
    """Handle no prose."""
    if doc.is_bibliography():
        return
    for heading, body in doc.main_sections():
        blocks = _meaningful(body)
        if not blocks:
            continue  # container heading: subsections follow
        if any(block.kind == "paragraph" for block in blocks):
            continue
        kinds = ", ".join(sorted({block.kind for block in blocks}))
        yield (
            heading.start,
            1,
            (
                f"раздел «{_short(heading)}» состоит только из вложений "
                f"({kinds}) — нужен абзац с разбором либо объединение с соседним "
                f"разделом"
            ),
        )


@rule("STRUCT004", "warning", "два вложения подряд без текста между ними")
def attachments_in_a_row(doc: Document) -> FileIssue:
    """Handle attachments in a row."""
    for _, body in doc.sections():
        blocks = [block for block in body if block.kind not in NOISE]
        for prev, cur in pairwise(blocks):
            if prev.kind in ATTACHMENT and cur.kind in ATTACHMENT:
                yield (
                    cur.start,
                    1,
                    (
                        "два вложения подряд — между ними нужен абзац, "
                        "объясняющий переход от первого ко второму"
                    ),
                )
