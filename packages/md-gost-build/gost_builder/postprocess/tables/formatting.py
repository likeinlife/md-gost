"""GOST borders, sizing, and alignment for data tables."""

from docx.document import Document as DocxDocument
from docx.table import Table

from gost_builder.postprocess.tables.kinds import is_formula_table
from gost_builder.postprocess.tables.properties import autofit_table, center_table, table_borders
from gost_builder.postprocess.tables.rows import format_table_rows


def _format_data_table(table: Table) -> None:
    table_borders(table)
    center_table(table)
    autofit_table(table)
    format_table_rows(table)


def fix_table_borders(doc: DocxDocument) -> None:
    """Apply the shared GOST appearance to data tables."""
    for table in doc.tables:
        if not is_formula_table(table):
            _format_data_table(table)
