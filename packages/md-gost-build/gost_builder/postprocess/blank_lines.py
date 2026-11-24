"""Create idempotent blank paragraphs around rendered blocks."""

from typing import Any

from docx.document import Document as DocxDocument
from docx.text.paragraph import Paragraph

from gost_builder.ooxml import WORD_TAG_PREFIX


def _blank_paragraph(sibling: Any) -> Any:
    """Build an empty single-spaced paragraph in the sibling namespace."""
    blank = sibling.makeelement(f"{WORD_TAG_PREFIX}p", {})
    paragraph_properties = blank.makeelement(f"{WORD_TAG_PREFIX}pPr", {})
    spacing = blank.makeelement(f"{WORD_TAG_PREFIX}spacing", {})
    spacing.set(f"{WORD_TAG_PREFIX}before", "0")
    spacing.set(f"{WORD_TAG_PREFIX}after", "0")
    spacing.set(f"{WORD_TAG_PREFIX}line", "240")  # одинарный интервал
    spacing.set(f"{WORD_TAG_PREFIX}lineRule", "auto")
    paragraph_properties.append(spacing)
    blank.append(paragraph_properties)
    return blank


def add_blank_line_after(el: Any, doc: DocxDocument) -> None:
    """Insert one empty single-spaced paragraph right after `el`.

    No-op when the next sibling is already an empty paragraph, so the pass is
    idempotent and does not stack blank lines on a rebuilt document.
    """
    nxt = el.getnext()
    if not _is_blank_paragraph(nxt, doc):
        el.addnext(_blank_paragraph(el))


def _is_blank_paragraph(element: Any, doc: DocxDocument) -> bool:
    if element is None or element.tag != f"{WORD_TAG_PREFIX}p":
        return False
    return not Paragraph(element, doc).text.strip()


def add_blank_line_before(el: Any, doc: DocxDocument) -> None:
    """Insert one empty single-spaced paragraph right before `el`, once."""
    previous = el.getprevious()
    if not _is_blank_paragraph(previous, doc):
        el.addprevious(_blank_paragraph(el))
