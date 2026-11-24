"""Reject data tables without a rendered caption."""

from typing import Any

from docx.document import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph

from gost_builder.errors import BuildError
from gost_builder.ooxml import WORD_TAG_PREFIX
from gost_builder.postprocess.styles import style_name
from gost_builder.postprocess.tables.kinds import is_formula_table

TABLE_CAPTION_PREVIEW_LENGTH = 70


def check_table_captions(doc: DocxDocument) -> None:
    """Every table must be introduced by a `Таблица N – ...` caption.

    A table without a caption cannot be referenced and breaks the numbering the
    reader expects, so this is an error rather than a warning: the caption is
    produced from the `<!-- #tbl:label Подпись -->` marker in the Markdown.
    """
    orphans: list[str] = []
    prev_caption = False
    for child in doc.element.body.iterchildren():
        prev_caption = _inspect_body_item(
            child,
            doc,
            prev_caption=prev_caption,
            orphans=orphans,
        )
    if orphans:
        raise BuildError(
            "ERROR: table without a caption (add `<!-- #tbl:label Подпись -->` "
            "right before it):\n  - " + "\n  - ".join(orphans),
        )


def _inspect_body_item(
    child: Any,
    doc: DocxDocument,
    orphans: list[str],
    *,
    prev_caption: bool,
) -> bool:
    if child.tag == f"{WORD_TAG_PREFIX}p":
        paragraph = Paragraph(child, doc)
        if paragraph.text.strip():
            return style_name(paragraph) == "GOSTTableCaption"
        return prev_caption
    if child.tag != f"{WORD_TAG_PREFIX}tbl":
        return prev_caption
    table = Table(child, doc)
    if not prev_caption and not is_formula_table(table):
        orphans.append(_table_preview(table))
    return False


def _table_preview(table: Table) -> str:
    cells = (cell.text.strip() for cell in table.rows[0].cells)
    return " | ".join(cells)[:TABLE_CAPTION_PREVIEW_LENGTH]
