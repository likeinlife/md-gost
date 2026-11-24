"""Update relationships, styles, and content types in a docx package."""

from lxml import etree
from lxml.etree import _Element as Element

from gost_builder.frame.constants import (
    CT,
    HEADER_CT,
    HEADER_REL,
    PART_DEFAULT,
    PART_FIRST,
    PR,
    STYLE_A3,
    STYLE_AE,
)
from gost_builder.frame.sections import word_tag

OVERRIDE_TAG = f"{{{CT}}}Override"
RELATIONSHIP_TAG = f"{{{PR}}}Relationship"


def add_content_types(xml_bytes: bytes) -> bytes:
    """Add content types."""
    tree = etree.fromstring(xml_bytes)
    existing = {override.get("PartName") for override in tree.findall(OVERRIDE_TAG)}
    for part in (PART_FIRST, PART_DEFAULT):
        pn = f"/{part}"
        if pn not in existing:
            ov = etree.SubElement(tree, OVERRIDE_TAG)
            ov.set("PartName", pn)
            ov.set("ContentType", HEADER_CT)
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)


def add_relationships(xml_bytes: bytes) -> tuple[bytes, str, str]:
    """Add relationships."""
    tree = etree.fromstring(xml_bytes)
    used_ids = _used_relationship_ids(tree)
    first_id, default_id = _header_ids(used_ids)
    _append_relationship(tree, first_id, PART_FIRST)
    _append_relationship(tree, default_id, PART_DEFAULT)
    payload = etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)
    return payload, first_id, default_id


def _used_relationship_ids(tree: Element) -> set[str]:
    identifiers = set()
    for node in tree.findall(RELATIONSHIP_TAG):
        identifiers.add(node.get("Id") or "")
    return identifiers


def _header_ids(used_ids: set[str]) -> tuple[str, str]:
    numbers = (_relationship_number(identifier) for identifier in used_ids)
    first_number = max(numbers, default=0) + 1
    second_number = first_number + 1
    return f"rId{first_number}", f"rId{second_number}"


def _relationship_number(identifier: str) -> int:
    if not identifier.startswith("rId") or not identifier[3:].isdigit():
        return 0
    return int(identifier[3:])


def _append_relationship(tree: Element, identifier: str, part: str) -> None:
    relationship = etree.SubElement(tree, RELATIONSHIP_TAG)
    relationship.set("Id", identifier)
    relationship.set("Type", HEADER_REL)
    relationship.set("Target", part.split("/", 1)[1])


def ensure_styles(xml_bytes: bytes) -> bytes:
    """Handle ensure styles."""
    tree = etree.fromstring(xml_bytes)
    have = set()
    for style_id in tree.findall(word_tag("style")):
        have.add(style_id.get(word_tag("styleId")))
    for sid, xml in (("a3", STYLE_A3), ("ae", STYLE_AE)):
        if sid not in have:
            tree.append(etree.fromstring(xml))
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)
