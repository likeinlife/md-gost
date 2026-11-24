"""Run the OOXML formatting passes on the document produced by Pandoc."""

import sys
from pathlib import Path

from docx import Document, document

from gost_builder.postprocess.caption_checks import check_table_captions
from gost_builder.postprocess.dashes import replace_emdash
from gost_builder.postprocess.layout import apply_layout
from gost_builder.postprocess.numbering import fix_numbering
from gost_builder.postprocess.paragraphs import fix_paragraphs
from gost_builder.postprocess.spacing import (
    blank_line_after_code,
    blank_line_after_image_captions,
    blank_line_after_tables,
    blank_lines_around_formulas,
)
from gost_builder.postprocess.tables.formatting import fix_table_borders
from gost_builder.postprocess.tables.formulas import format_formula_tables


def _apply_content_passes(doc: document.Document) -> None:
    replace_emdash(doc)
    fix_paragraphs(doc)
    fix_table_borders(doc)
    format_formula_tables(doc)
    check_table_captions(doc)
    blank_line_after_tables(doc)
    blank_lines_around_formulas(doc)
    blank_line_after_code(doc)
    blank_line_after_image_captions(doc)


def postprocess(path: Path, *, page_break_before_h1: bool = True) -> None:
    """Apply the document formatting passes to the generated file in place."""
    doc = Document(str(path))
    try:
        fix_numbering(doc)
    except Exception as error:  # noqa: BLE001 — numbering part may be absent
        sys.stdout.write(f"WARN numbering: {error}\n")
    _apply_content_passes(doc)
    apply_layout(doc, page_break=page_break_before_h1)
    doc.save(str(path))
    sys.stdout.write(f"postprocess done: {path}\n")
