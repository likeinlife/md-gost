"""Require a caption marker before each table."""

import re
from collections.abc import Iterator

from gost_lint.markdown import Block, Document
from gost_lint.markdown.adjacent_blocks import with_previous
from gost_lint.rules.registry import rule

FileIssue = Iterator[tuple[int, int, str]]
CAPTION_HEADING = re.compile(r"^\s*Таблица\b", re.IGNORECASE)


@rule("REF001", "error", "таблица без маркера-подписи")
def table_without_caption(doc: Document) -> FileIssue:
    """Handle table without caption."""
    blocks = [block for block in doc.blocks if block.kind != "comment"]
    for previous, block in with_previous(blocks):
        if block.kind == "table" and not _has_caption(previous):
            yield (
                block.start,
                1,
                "таблица без подписи — перед ней нужен маркер <!-- #tbl:label Подпись -->",
            )


def _has_caption(previous: Block | None) -> bool:
    if previous is None:
        return False
    if previous.kind == "table_marker":
        return True
    subsection_level = 3
    if previous.kind != "heading" or previous.level < subsection_level:
        return False
    title = previous.meta.get("title", "")
    return bool(CAPTION_HEADING.match(title))
