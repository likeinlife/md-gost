"""Recognize formula tables from the styles assigned by the Pandoc filter."""

from docx.table import Table

from gost_builder.postprocess.styles import style_name

FORMULA_STYLE = "GOSTFormula"
EXPLANATION_STYLE = "GOSTExplanation"


def is_formula_table(table: Table) -> bool:
    """Check for the formula style in the first row, above any explanation."""
    return any(
        style_name(paragraph) == FORMULA_STYLE
        for cell in table.rows[0].cells
        for paragraph in cell.paragraphs
    )
