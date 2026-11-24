"""Text to show an author for a labelled Markdown object."""

from pathlib import PurePosixPath

from gost_lint.markdown import Block, Document
from gost_lint.markdown.syntax import MATH_DELIM


def title_for(document: Document, block: Block) -> str:
    """Handle title for."""
    caption = block.meta.get("caption") or block.meta.get("text")
    if caption:
        return caption
    if block.kind == "eq_marker":
        return _expression(document, block)
    if block.kind == "listing" and block.meta.get("src"):
        return PurePosixPath(block.meta["src"]).name
    if block.kind in {"image", "diagram", "listing"}:
        return _section(document, block)
    return ""


def _expression(document: Document, marker: Block) -> str:
    after_marker = (block for block in document.blocks if block.start > marker.end)
    following = next(after_marker, None)
    if following is None or following.kind != "formula":
        return ""
    return following.text.strip().removeprefix(MATH_DELIM).removesuffix(MATH_DELIM).strip()


def _section(document: Document, target: Block) -> str:
    for heading in reversed(document.of_kind("heading")):
        if heading.start < target.start:
            return heading.meta["title"]
    return ""
