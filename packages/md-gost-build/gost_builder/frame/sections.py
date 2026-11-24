"""Edit page geometry and header references in section XML."""

from lxml import etree
from lxml.etree import _Element as Element

from gost_builder.frame.geometry import PG_MAR, PG_SZ
from gost_builder.ooxml import RELATIONSHIPS_NAMESPACE, WORD_NAMESPACE


def word_tag(tag: str) -> str:
    """Handle word tag."""
    return f"{{{WORD_NAMESPACE}}}{tag}"


def get_or_make(parent: Element, tag: str) -> Element:
    """Return or make."""
    element = parent.find(word_tag(tag))
    if element is None:
        element = etree.SubElement(parent, word_tag(tag))
    return element


def configure_section(section: Element, first_id: str | None, default_id: str) -> None:
    """Configure section."""
    _set_geometry(section)
    _set_headers(section, first_id, default_id)
    if first_id is not None:
        get_or_make(section, "titlePg").attrib.pop(word_tag("val"), None)


def _set_geometry(section: Element) -> None:
    for tag, attributes in (("pgSz", PG_SZ), ("pgMar", PG_MAR)):
        element = get_or_make(section, tag)
        for key, setting in attributes.items():
            element.set(word_tag(key), setting)


def _set_headers(section: Element, first_id: str | None, default_id: str) -> None:
    for tag in ("headerReference", "footerReference"):
        for reference in section.findall(word_tag(tag)):
            section.remove(reference)
    for kind, relationship_id in (("default", default_id), ("first", first_id)):
        if relationship_id is None:
            continue
        header = etree.SubElement(section, word_tag("headerReference"))
        header.set(word_tag("type"), kind)
        header.set(f"{{{RELATIONSHIPS_NAMESPACE}}}id", relationship_id)


def set_page_start(section: Element, page_start: int) -> None:
    """Set page start."""
    numbering = get_or_make(section, "pgNumType")
    numbering.set(word_tag("start"), str(page_start))
