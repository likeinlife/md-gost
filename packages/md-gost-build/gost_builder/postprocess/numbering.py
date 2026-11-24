"""List marker and run font formatting."""

import sys
from typing import Any

from docx.document import Document as DocxDocument
from docx.shared import Pt
from docx.text.run import Run

from gost_builder.ooxml import WORD_TAG_PREFIX
from gost_builder.postprocess.dashes import EN_DASH

FONT = "Times New Roman"

BODY_FONT_SIZE = 14

INDENT_TWIPS = 709  # 1.25 cm in twips (1.25 * 567)


def _set_rfonts(rpr: Any) -> Any:
    rfonts = rpr.find(f"{WORD_TAG_PREFIX}rFonts")
    if rfonts is None:
        rfonts = rpr.makeelement(f"{WORD_TAG_PREFIX}rFonts", {})
        rpr.insert(0, rfonts)
    for attribute in ("ascii", "hAnsi", "cs"):
        rfonts.set(f"{WORD_TAG_PREFIX}{attribute}", FONT)
    return rfonts


def set_marker_indent(ppr: Any) -> None:
    """Marker/first line at 1.25 cm, wrapped lines flush left (0)."""
    ind = ppr.find(f"{WORD_TAG_PREFIX}ind")
    if ind is None:
        ind = ppr.makeelement(f"{WORD_TAG_PREFIX}ind", {})
        ppr.append(ind)
    ind.set(f"{WORD_TAG_PREFIX}left", "0")
    ind.set(f"{WORD_TAG_PREFIX}firstLine", str(INDENT_TWIPS))
    ind.attrib.pop(f"{WORD_TAG_PREFIX}hanging", None)


def _format_numbering_level(level: Any) -> None:
    numfmt = level.find(f"{WORD_TAG_PREFIX}numFmt")
    if numfmt is not None and numfmt.get(f"{WORD_TAG_PREFIX}val") == "bullet":
        marker = level.find(f"{WORD_TAG_PREFIX}lvlText")
        if marker is None:
            marker = level.makeelement(f"{WORD_TAG_PREFIX}lvlText", {})
            level.append(marker)
        marker.set(f"{WORD_TAG_PREFIX}val", EN_DASH)
    run_properties = _get_or_create(level, "rPr")
    _set_rfonts(run_properties)
    _set_run_size(level, run_properties)
    paragraph_properties = _get_or_create(level, "pPr")
    set_marker_indent(paragraph_properties)


def _get_or_create(element: Any, tag: str) -> Any:
    child = element.find(f"{WORD_TAG_PREFIX}{tag}")
    if child is not None:
        return child
    child = element.makeelement(f"{WORD_TAG_PREFIX}{tag}", {})
    element.append(child)
    return child


def _set_run_size(level: Any, run_properties: Any) -> None:
    for tag in ("sz", "szCs"):
        size = level.find(f"{WORD_TAG_PREFIX}rPr/{WORD_TAG_PREFIX}{tag}")
        if size is None:
            size = run_properties.makeelement(f"{WORD_TAG_PREFIX}{tag}", {})
            run_properties.append(size)
        size.set(f"{WORD_TAG_PREFIX}val", "28")


def fix_numbering(doc: DocxDocument) -> None:
    """Set list markers and numbering to GOST formatting."""
    try:
        levels = doc.part.numbering_part.element.iter(f"{WORD_TAG_PREFIX}lvl")
    except Exception as error:  # noqa: BLE001 — numbering part may be absent
        sys.stdout.write(f"WARN no numbering part: {error}\n")
        return
    for level in levels:
        _format_numbering_level(level)


def set_run_font(run: Run, size: int = 14, *, italic: bool | None = None) -> None:
    """Set run font."""
    run.font.name = FONT
    run.font.size = Pt(size)
    if italic is not None:
        run.font.italic = italic
    _set_rfonts(run._element.get_or_add_rPr())
