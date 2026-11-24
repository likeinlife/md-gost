"""Assertions shared by formula table tests."""

import re

from test_helpers import W_T

TABLE_TAG = "<w:tbl>"


def _assert_formula_numbers(document: str) -> None:
    formula_count = 2
    assert document.count(TABLE_TAG) == formula_count, "формулы не разложены по таблицам"
    assert document.count("<m:oMath") >= formula_count, "формула не превратилась в OMML"
    text = "".join(W_T.findall(document))
    assert "(1)" in text, "формулы не получили номеров"
    assert "(2)" in text, "формулы не получили номеров"
    assert "по формуле (1)" in text, "[@eq:k] не разрешилась в номер в скобках"
    _assert_formula_styles(document)


def _assert_formula_styles(document: str) -> None:
    assert 'w:val="GOSTFormula"' in document
    assert 'w:val="GOSTFormulaNumber"' in document


def _assert_formula_geometry(document: str) -> None:
    formula_table = document[document.find(TABLE_TAG) : document.find("</w:tbl>")]
    assert 'w:val="none"' in formula_table, "у таблицы с формулой остались границы"
    assert "<w:cantSplit/>" in formula_table, "строку с формулой можно разорвать по страницам"
    # Колонки по краям равны: формула встаёт по центру страницы, а не по
    # центру места, оставшегося от номера.
    columns = re.findall(r'<w:gridCol w:w="(\d+)"/>', formula_table)
    column_count = 3
    assert len(columns) == column_count, f"ожидались три колонки: {columns}"
    assert columns[0] == columns[2], f"колонки несимметричны: {columns}"


def _assert_explanation_content(rows: list[str]) -> None:
    row_count = 3
    assert len(rows) == row_count, "экспликация не легла строками в таблицу формулы"
    assert "GOSTFormula" in rows[0]
    explanation = "".join(W_T.findall(rows[1]))
    assert "где" in explanation
    assert 'w:val="GOSTExplanation"' in rows[1]


def _assert_explanation_layout(rows: list[str]) -> None:
    assert rows[1].count('<w:gridSpan w:val="2"/>') == 1
    justified_cells = 2
    assert rows[1].count('<w:jc w:val="both"/>') == justified_cells, "расшифровка не по ширине"
    assert "где" not in "".join(W_T.findall(rows[2])), "«где» повторилось на второй строке"


def _is_blank(block: str) -> bool:
    is_paragraph = block.startswith("<w:p")
    is_empty = not "".join(W_T.findall(block)).strip()
    return is_paragraph and is_empty
