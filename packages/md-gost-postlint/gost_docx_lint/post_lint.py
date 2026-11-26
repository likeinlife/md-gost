#!/usr/bin/env python3
"""Inspect generated DOCX OOXML for layout risks that Markdown lint cannot see."""

from __future__ import annotations

import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
NS = {"w": W, "wp": WP}
EMU_PER_TWIP = 635
_ROWS_LISTED = 5
_START_BLOCK_DATA_ROWS = 2
_TALL_IMAGE_SHARE = 0.65
_A4_HEIGHT_TWIPS = 15840
_DEFAULT_MARGIN_TWIPS = 1440
_PERCENT = 100


@dataclass(frozen=True)
class Finding:
    """One layout warning found in a generated document."""

    code: str
    message: str


def _twips(element: ET.Element | None, attribute: str, default: int) -> int:
    if element is None:
        return default
    value = element.get(f"{{{W}}}{attribute}")
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


def _page_height_emu(root: ET.Element) -> tuple[int, int]:
    """Return printable page height and a conservative page height in EMUs."""
    section = root.find(".//w:sectPr", NS)
    page = section.find("w:pgSz", NS) if section is not None else None
    margins = section.find("w:pgMar", NS) if section is not None else None
    height_twips = _twips(page, "h", _A4_HEIGHT_TWIPS)
    top = _twips(margins, "top", _DEFAULT_MARGIN_TWIPS)
    bottom = _twips(margins, "bottom", _DEFAULT_MARGIN_TWIPS)
    printable = max(height_twips - top - bottom, 1) * EMU_PER_TWIP
    return printable, height_twips * EMU_PER_TWIP


def _style_names(styles_root: ET.Element) -> dict[str, str]:
    return {
        style.get(f"{{{W}}}styleId", ""): name.get(f"{{{W}}}val", "")
        for style in styles_root.findall("w:style", NS)
        if (name := style.find("w:name", NS)) is not None
    }


def _paragraph_style(paragraph: ET.Element, style_names: dict[str, str]) -> str:
    style = paragraph.find("w:pPr/w:pStyle", NS)
    if style is None:
        return ""
    return style_names.get(style.get(f"{{{W}}}val", ""), "")


def _has_paragraph_property(paragraph: ET.Element, property_name: str) -> bool:
    return paragraph.find(f"w:pPr/w:{property_name}", NS) is not None


def _caption_findings(
    body_children: list[ET.Element],
    style_names: dict[str, str],
) -> list[Finding]:
    findings: list[Finding] = []
    for child_index, child in enumerate(body_children):
        if child.tag != f"{{{W}}}p":
            continue
        findings.extend(_caption_finding(body_children, style_names, child_index, child))
    return findings


def _caption_finding(
    body_children: list[ET.Element],
    style_names: dict[str, str],
    child_index: int,
    child: ET.Element,
) -> list[Finding]:
    style = _paragraph_style(child, style_names)
    findings: list[Finding] = []
    if style in {"GOSTTableCaption", "GOSTListingCaption"} and not _has_paragraph_property(
        child,
        "keepNext",
    ):
        label = "подпись таблицы" if style == "GOSTTableCaption" else "подпись листинга"
        findings.append(Finding("POST005", f"{label} не удерживается вместе с объектом"))
    if style == "GOSTImageCaption" and not _image_caption_kept(body_children, child_index, child):
        findings.append(
            Finding("POST006", "подпись рисунка не удерживается вместе с изображением"),
        )
    return findings


def _image_caption_kept(
    body_children: list[ET.Element],
    child_index: int,
    child: ET.Element,
) -> bool:
    previous = body_children[child_index - 1] if child_index else None
    image_precedes = previous is not None and _contains_image(previous)
    image_kept = previous is not None and _has_paragraph_property(previous, "keepNext")
    caption_kept = _has_paragraph_property(child, "keepLines")
    return image_precedes and image_kept and caption_kept


def _contains_image(paragraph: ET.Element) -> bool:
    if paragraph.tag != f"{{{W}}}p":
        return False
    return any(paragraph.find(path, NS) is not None for path in (".//w:drawing", ".//w:pict"))


def _table_findings(root: ET.Element) -> list[Finding]:
    findings: list[Finding] = []
    for index, table in enumerate(root.findall(".//w:tbl", NS), start=1):
        findings.extend(_one_table(index, table))
    return findings


def _one_table(index: int, table: ET.Element) -> list[Finding]:
    styles = {
        style.get(f"{{{W}}}val", "") for style in table.findall(".//w:tc/w:p/w:pPr/w:pStyle", NS)
    }
    if "GOSTFormula" in styles:
        return _formula_findings(index, table)
    return [
        *_split_findings(index, table),
        *_header_findings(index, table),
        *_start_block_findings(index, table),
    ]


def _formula_findings(index: int, table: ET.Element) -> list[Finding]:
    formula_row = table.find("w:tr", NS)
    if formula_row is None or _row_keeps_next(formula_row):
        return []
    return [Finding("POST007", f"формула в таблице {index} не удерживается с пояснением")]


def _row_keeps_next(row: ET.Element) -> bool:
    return all(
        paragraph.find("w:pPr/w:keepNext", NS) is not None
        for paragraph in row.findall(".//w:tc/w:p", NS)
    )


def _split_findings(index: int, table: ET.Element) -> list[Finding]:
    rows = table.findall("w:tr", NS)
    splittable = _splittable_rows(rows)
    if not rows or not splittable:
        return []
    row_list = ", ".join(map(str, splittable[:_ROWS_LISTED]))
    suffix = "…" if len(splittable) > _ROWS_LISTED else ""
    message = f"таблица {index}: строки {row_list}{suffix} могут разрываться между страницами"
    return [Finding("POST001", message)]


def _splittable_rows(rows: list[ET.Element]) -> list[int]:
    splittable: list[int] = []
    for row_number, row in enumerate(rows, start=1):
        properties = row.find("w:trPr", NS)
        if properties is None or properties.find("w:cantSplit", NS) is None:
            splittable.append(row_number)
    return splittable


def _header_findings(index: int, table: ET.Element) -> list[Finding]:
    rows = table.findall("w:tr", NS)
    header_rows = [row for row in rows if row.find("w:trPr/w:tblHeader", NS) is not None]
    findings: list[Finding] = []
    for row_number, row in enumerate(header_rows, start=1):
        if _row_keeps_next(row):
            continue
        message = (
            f"таблица {index}: строка шапки {row_number} не удерживается "
            "вместе со следующей строкой таблицы"
        )
        findings.append(Finding("POST004", message))
    return findings


def _start_block_findings(index: int, table: ET.Element) -> list[Finding]:
    rows = table.findall("w:tr", NS)
    first_data_index = _header_end(rows) + 1
    if first_data_index + _START_BLOCK_DATA_ROWS >= len(rows):
        return []
    first_rows = rows[first_data_index : first_data_index + _START_BLOCK_DATA_ROWS]
    if all(_row_keeps_next(row) for row in first_rows):
        return []
    message = f"таблица {index}: стартовый блок не удерживает первые три строки данных"
    return [Finding("POST008", message)]


def _header_end(rows: list[ET.Element]) -> int:
    header_end = 0
    for row_index, row in enumerate(rows):
        if row_index == 0 or row.find("w:trPr/w:tblHeader", NS) is not None:
            header_end = row_index
            continue
        break
    return header_end


def _image_findings(root: ET.Element, printable_height: int, page_height: int) -> list[Finding]:
    findings: list[Finding] = []
    for index, extent in enumerate(root.findall(".//wp:extent", NS), start=1):
        findings.extend(_image_extent(index, extent, printable_height, page_height))
    return findings


def _image_extent(
    index: int,
    extent: ET.Element,
    printable_height: int,
    page_height: int,
) -> list[Finding]:
    image_height = _extent_height(extent)
    if image_height is None:
        return []
    findings: list[Finding] = []
    if image_height > printable_height * _TALL_IMAGE_SHARE:
        percent = round(image_height / printable_height * _PERCENT)
        message = (
            f"изображение {index} занимает около {percent}% печатной высоты страницы; "
            "проверьте заполненность страницы и масштаб"
        )
        findings.append(Finding("POST002", message))
    if image_height > page_height:
        message = f"изображение {index} выше физической страницы и может вытеснить соседний текст"
        findings.append(Finding("POST003", message))
    return findings


def _extent_height(extent: ET.Element) -> int | None:
    try:
        return int(extent.get("cy", "0"))
    except ValueError:
        return None


def inspect_docx(path: Path) -> list[Finding]:
    """Read document.xml and report verifiable OOXML layout risks."""
    with zipfile.ZipFile(path) as package:
        root = ET.fromstring(package.read("word/document.xml"))
        styles_root = ET.fromstring(package.read("word/styles.xml"))
    style_names = _style_names(styles_root)
    body = root.find(".//w:body", NS)
    body_children = list(body) if body is not None else []
    printable_height, page_height = _page_height_emu(root)
    return [
        *_caption_findings(body_children, style_names),
        *_table_findings(root),
        *_image_findings(root, printable_height, page_height),
    ]


def check(path: Path) -> int:
    """Print OOXML findings for one DOCX and return the process status."""
    if not path.is_file() or path.suffix.lower() != ".docx":
        sys.stderr.write(f"md-gost postlint: ожидается существующий .docx: {path}\n")
        return 2
    try:
        findings = inspect_docx(path)
    except (OSError, KeyError, ET.ParseError, zipfile.BadZipFile) as error:
        sys.stderr.write(f"md-gost postlint: не удалось прочитать OOXML {path}: {error}\n")
        return 2
    for finding in findings:
        sys.stdout.write(f"{path}: warning [{finding.code}] {finding.message}\n")
    if findings:
        sys.stdout.write(f"md-gost postlint: замечаний — {len(findings)}\n")
    else:
        sys.stdout.write("md-gost postlint: замечаний нет\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the command."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        sys.stderr.write("usage: md-gost postlint <document.docx>\n")
        return 2
    return check(Path(args[0]))


if __name__ == "__main__":
    raise SystemExit(main())
