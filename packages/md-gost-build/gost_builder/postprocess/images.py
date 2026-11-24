"""Center and scale inline images to fit the page."""

import sys
from collections.abc import Iterator
from typing import Any

from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shape import InlineShape
from docx.shared import Cm, Emu
from docx.text.paragraph import Paragraph


def has_picture(paragraph: Paragraph) -> bool:
    """Return whether picture."""
    xml = paragraph._p.xml
    return "<w:drawing" in xml or "<w:pict" in xml or "<pic:pic" in xml


def center_images(doc: DocxDocument) -> None:
    """Center any paragraph that contains an inline image (w:drawing/w:pict)."""
    for paragraph in doc.paragraphs:
        if has_picture(paragraph):
            paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.first_line_indent = Cm(0)


CAPTION_ALLOWANCE_CM = 1.2

CAPTION_ALLOWANCE = Cm(CAPTION_ALLOWANCE_CM)
ImageLimits = tuple[int, int]
ImageWithLimits = tuple[InlineShape, ImageLimits]


def fit_images(doc: DocxDocument) -> int:
    """Shrink pictures that do not fit the text area, keeping the aspect ratio.

    PlantUML renders at its own scale and a wide diagram easily comes out twice
    the page width: Word then crops it at the right margin instead of scaling.
    Only oversized images are touched — a small picture keeps its natural size.
    """
    resized = (_scale_image(shape, *limits) for shape, limits in _images_with_limits(doc))
    scaled = sum(resized)
    if scaled:
        sys.stdout.write(f"fit images: scaled down {scaled}\n")
    return scaled


def _images_with_limits(doc: DocxDocument) -> Iterator[ImageWithLimits]:
    # A section's geometry is carried by its last paragraph, or by the final
    # body-level sectPr. Walking backwards keeps tables and other containers
    # with the section that contains them.
    sections = iter(reversed(list(doc.sections)))
    limits = _image_limits(next(sections))
    section_break = f"{qn('w:pPr')}/{qn('w:sectPr')}"
    for node in reversed(doc._element.body):
        if node.find(section_break) is not None:
            limits = _image_limits(next(sections))
        if limits is not None:
            for inline in node.iter(qn("wp:inline")):
                yield InlineShape(inline), limits


def _image_limits(section: Any) -> ImageLimits | None:
    if not _has_page_geometry(section):
        return None
    max_width = section.page_width - section.left_margin - section.right_margin
    max_height = section.page_height - section.top_margin - section.bottom_margin
    return max_width, max_height - CAPTION_ALLOWANCE


def _has_page_geometry(section: Any) -> bool:
    return all(
        dimension is not None
        for dimension in (
            section.page_width,
            section.page_height,
            section.left_margin,
            section.right_margin,
            section.top_margin,
            section.bottom_margin,
        )
    )


def _scale_image(shape: Any, max_w: int, max_h: int) -> int:
    width, height = shape.width, shape.height
    if not width or not height or (width <= max_w and height <= max_h):
        return 0
    factor = min(max_w / width, max_h / height)
    shape.width = Emu(int(width * factor))
    shape.height = Emu(int(height * factor))
    return 1
