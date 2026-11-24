"""Configure all document styles for a Pandoc reference document."""

from docx.document import Document as DocxDocument

from gost_builder.reference.captions import apply_caption_styles
from gost_builder.reference.formulas import apply_formula_styles
from gost_builder.reference.layout import apply_code_styles, apply_compact_styles, set_page_geometry
from gost_builder.reference.links import apply_link_styles
from gost_builder.reference.paragraphs import apply_heading_styles, apply_toc_style, set_body_styles


def apply_styles(doc: DocxDocument) -> None:
    """Apply styles."""
    styles = doc.styles
    normal = set_body_styles(styles)
    apply_caption_styles(styles, normal)
    apply_formula_styles(styles, normal)
    apply_heading_styles(styles)
    apply_toc_style(styles)
    apply_link_styles(styles)
    apply_code_styles(styles)
    apply_compact_styles(styles)
    set_page_geometry(doc)
