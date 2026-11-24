"""Check merged cells and grid spans in rendered table XML."""

from types import MappingProxyType
from typing import cast
from xml.etree import ElementTree as ET

W_NS = cast(
    "dict[str, str]",
    MappingProxyType({"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}),
)
W_ATTR = f"{{{W_NS['w']}}}"
VALUE_ATTR = f"{W_ATTR}val"


def _assert_bold_runs(paragraph: ET.Element) -> None:
    for run in paragraph.findall("w:r", W_NS):
        bold = run.find("w:rPr/w:b", W_NS)
        assert bold is not None
        assert bold.get(VALUE_ATTR) != "0"


def _assert_grid_spans(table: ET.Element) -> None:
    spans = table.findall(".//w:gridSpan", W_NS)
    assert any(element.get(VALUE_ATTR) == "2" for element in spans)
    merge_count = 6
    assert len(table.findall(".//w:vMerge", W_NS)) == merge_count


def assert_grid_cell_spans(root: ET.Element) -> None:
    rows = root.findall("w:body/w:tbl/w:tr", W_NS)
    cell = rows[1].find("w:tc", W_NS)
    assert cell is not None
    colspan = cell.find("w:tcPr/w:gridSpan", W_NS)
    rowspan = cell.find("w:tcPr/w:vMerge", W_NS)
    assert colspan is not None
    assert colspan.get(VALUE_ATTR) == "2"
    assert rowspan is not None
    assert rowspan.get(VALUE_ATTR) == "restart"
