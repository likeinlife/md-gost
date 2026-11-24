"""Shared checks for grid-table rendering tests."""

from xml.etree import ElementTree as ET

from grid_span_helpers import VALUE_ATTR, W_NS, _assert_bold_runs, _assert_grid_spans


def make_grid_body(grid_table: str) -> str:
    return (
        "# Глава 1. Планирование\n\n## 1.1 Результаты\n\n"
        "Данные приведены в таблицах [@tbl:plain] и [@tbl:plan].\n\n"
        "<!-- #tbl:plain Обычная таблица -->\n\n"
        "| А | Б |\n|---|---|\n| 1 | 2 |\n\n"
        "Обычная таблица показывает исходные данные.\n\n"
        "<!-- #tbl:plan План и факт по этапам -->\n\n"
        + grid_table
        + "\nПлан интервью перевыполнен, сбор требований требует дополнительного времени.\n"
    )


def assert_grid_document(root: ET.Element) -> None:
    text = "".join(root.itertext())
    assert "Таблица 1 – Обычная таблица" in text
    assert "Таблица 2 – План и факт по этапам" in text
    assert "в таблицах 1 и 2." in text
    tables = root.findall("w:body/w:tbl", W_NS)
    table_count = 2
    row_count = 4
    assert len(tables) == table_count
    rows = tables[1].findall("w:tr", W_NS)
    assert len(rows) == row_count
    _assert_header_rows(rows[:2])
    _assert_body_rows(rows[2:])
    _assert_grid_spans(tables[1])


def _assert_header_rows(rows: list[ET.Element]) -> None:
    for row in rows:
        assert row.find("w:trPr/w:tblHeader", W_NS) is not None
        _assert_header_cells(row)


def _assert_header_cells(row: ET.Element) -> None:
    for cell in row.findall("w:tc", W_NS):
        for paragraph in cell.findall("w:p", W_NS):
            if not paragraph.findall("w:r", W_NS):
                continue
            alignment = paragraph.find("w:pPr/w:jc", W_NS)
            assert alignment is not None
            assert alignment.get(VALUE_ATTR) == "center"
            _assert_bold_runs(paragraph)


def _assert_body_rows(rows: list[ET.Element]) -> None:
    for row in rows:
        assert row.find("w:trPr/w:tblHeader", W_NS) is None
        assert row.find(".//w:rPr/w:b", W_NS) is None
