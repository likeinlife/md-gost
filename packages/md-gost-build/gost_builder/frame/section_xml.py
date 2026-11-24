"""Edit document XML to apply the GOST frame geometry and headers."""

from lxml import etree
from lxml.etree import _Element as Element

from gost_builder.frame.geometry import SECTPR_ORDER
from gost_builder.frame.sections import configure_section, set_page_start, word_tag
from gost_builder.ooxml import APPENDIX_HEADER_ID, RELATIONSHIPS_NAMESPACE


def reorder_sectpr(section: Element) -> None:
    """Handle reorder sectpr."""
    children = sorted(
        section,
        key=lambda element: (
            SECTPR_ORDER.index(etree.QName(element).localname)
            if etree.QName(element).localname in SECTPR_ORDER
            else len(SECTPR_ORDER)
        ),
    )
    for child in list(section):
        section.remove(child)
    for child in children:
        section.append(child)


def edit_document(xml_bytes: bytes, rid_first: str, rid_default: str, page_start: int) -> bytes:
    """Handle edit document."""
    tree = etree.fromstring(xml_bytes)
    for index, section in enumerate(tree.findall(f".//{word_tag('sectPr')}")):
        if not _is_appendix(section):
            configure_section(section, rid_first if index == 0 else None, rid_default)
        if index == 0:
            set_page_start(section, page_start)
        reorder_sectpr(section)
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)


def _is_appendix(section: Element) -> bool:
    identifier = f"{{{RELATIONSHIPS_NAMESPACE}}}id"
    refs = section.findall(word_tag("headerReference"))
    return any(header.get(identifier) == APPENDIX_HEADER_ID for header in refs)
