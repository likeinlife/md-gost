"""Check caption capitalization and punctuation."""

from collections.abc import Iterator

from gost_lint.markdown import Block, Document
from gost_lint.rules.registry import rule

FileIssue = Iterator[tuple[int, int, str]]
CAPTION_PREVIEW_LENGTH = 40


@rule("STYLE003", "warning", "плохо оформленная подпись")
def caption_form(doc: Document) -> FileIssue:
    """Handle caption form."""
    for block in doc.blocks:
        yield from _caption_issues(block)


def _caption_issues(block: Block) -> FileIssue:
    caption = block.meta.get("caption")
    if caption is None or block.kind == "code":
        return
    label = block.meta.get("label", block.kind)
    if not caption.strip():
        yield (block.start, 1, f"пустая подпись у {label}")
        return
    yield from _punctuation_issue(block, caption)
    yield from _capitalization_issue(block, caption)


def _punctuation_issue(block: Block, caption: str) -> FileIssue:
    if caption.rstrip().endswith("."):
        excerpt = caption[:CAPTION_PREVIEW_LENGTH]
        message = f"подпись «{excerpt}» кончается точкой — точка в подписи не ставится"
        yield (block.start, 1, message)


def _capitalization_issue(block: Block, caption: str) -> FileIssue:
    first = caption.lstrip()[0]
    if first.isalpha() and first.islower():
        excerpt = caption[:CAPTION_PREVIEW_LENGTH]
        yield (block.start, 1, f"подпись «{excerpt}» начинается со строчной буквы")
