"""Inspect paragraph styles assigned by Pandoc."""

from docx.text.paragraph import Paragraph


def style_name(paragraph: Paragraph) -> str:
    """Handle style name."""
    return (paragraph.style.name or "") if paragraph.style else ""
