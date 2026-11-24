"""Fill and load the reusable frame header templates."""

import re
from pathlib import Path
from types import MappingProxyType

from lxml import etree

from gost_builder.errors import BuildError
from gost_builder.frame.settings import FrameSettings
from gost_builder.ooxml import WORD_NAMESPACE

FRAME = Path(__file__).resolve().parent / "templates"

PLACEHOLDERS = MappingProxyType(
    {
        "{{TITLE}}": "title",
        "{{DESIGNATION}}": "designation",
        "{{AUTHOR}}": "author",
        "{{CHECKER}}": "checker",
        "{{ORG}}": "org",
        "{{SHEETS}}": "sheets",
        "{{FIRST_SHEET}}": "first_sheet",
    },
)
LEFTOVER = re.compile(r"\{\{[A-Z_]+\}\}")


def substitute(xml_bytes: bytes, frame_settings: FrameSettings) -> bytes:
    """Fill placeholders in a frame template in one pass."""
    tree = etree.fromstring(xml_bytes)
    for node in tree.findall(f".//{{{WORD_NAMESPACE}}}t"):
        node.text = _replace_fields(node.text, frame_settings)
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)


def _replace_fields(text: str | None, frame_settings: FrameSettings) -> str | None:
    if not text:
        return text
    if "{{" not in text:
        return text
    for token, key in PLACEHOLDERS.items():
        text = text.replace(token, str(frame_settings[key]))
    leftover = LEFTOVER.search(text)
    if leftover:
        message = f"add_frame: unknown placeholder {leftover.group(0)} in frame template"
        raise BuildError(message)
    return text


def build_headers(frame_settings: FrameSettings) -> tuple[bytes, bytes]:
    """Build headers."""
    first = substitute((FRAME / "header_first.xml").read_bytes(), frame_settings)
    default = substitute((FRAME / "header_default.xml").read_bytes(), frame_settings)
    return first, default
