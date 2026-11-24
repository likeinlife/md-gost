"""Replace em dashes across all text-bearing document parts."""

from typing import Any

from docx.document import Document as DocxDocument
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from lxml import etree

from gost_builder.ooxml import WORD_TAG_PREFIX

EM_DASH = "\u2014"  # — long dash, not allowed in the output

EN_DASH = "\u2013"  # – short dash, GOST body/caption dash

TEXT_RELTYPES = (RT.HEADER, RT.FOOTER, RT.FOOTNOTES, RT.ENDNOTES, RT.COMMENTS)


def _fix_dashes_in(element: Any) -> int:
    """Replace em-dash with en-dash in every w:t descendant of `element`."""
    count = 0
    for text_node in element.iter(f"{WORD_TAG_PREFIX}t"):
        if text_node.text and EM_DASH in text_node.text:
            text_node.text = text_node.text.replace(EM_DASH, EN_DASH)
            count += 1
    return count


def _fix_dashes_in_part(part: Any) -> int:
    """Patch one related part, whichever form python-docx gave it.

    Anys it parses (headers, footers, comments) are edited in place. Ones it
    keeps as raw bytes (footnotes, endnotes) are parsed, patched and written
    back through `_blob` — python-docx offers no public setter, and serialising
    the package re-reads that attribute.
    """
    element = getattr(part, "element", None)
    if element is not None:
        return _fix_dashes_in(element)

    blob = part.blob
    if not blob or EM_DASH.encode("utf-8") not in blob:
        return 0
    tree = etree.fromstring(blob)
    count = _fix_dashes_in(tree)
    if count:
        part._blob = etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)
    return count


def replace_emdash(doc: DocxDocument) -> int:
    """Em-dash -> en-dash across the whole package.

    Walks the XML rather than python-docx's paragraph/table API: iterating w:t
    nodes also reaches nested tables, text boxes and footnotes, none of which
    the API view exposes. Related parts come from the existing relationships,
    so reading them cannot create an empty header/footer part as a side effect.
    """
    count = _fix_dashes_in(doc.element.body)
    for rel in doc.part.rels.values():
        if rel.is_external or rel.reltype not in TEXT_RELTYPES:
            continue
        count += _fix_dashes_in_part(rel.target_part)
    return count
