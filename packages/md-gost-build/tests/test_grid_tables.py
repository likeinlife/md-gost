import zipfile
from xml.etree import ElementTree as ET

import pytest
from conftest import BuiltFactory, WorkFactory, needs_pandoc
from grid_helpers import (
    assert_grid_document,
    make_grid_body,
)
from grid_span_helpers import assert_grid_cell_spans

pytestmark = [needs_pandoc, pytest.mark.build]

GRID_TABLE = """+--------------+------------------+---------------------+
| Этап         | Показатель       | Значение            |
|              |                  +----------+----------+
|              |                  | План     | Факт     |
+==============+==================+==========+==========+
| Анализ       | Интервью         | 10       | 12       |
|              +------------------+----------+----------+
|              | Требования       | 20       | 18       |
+--------------+------------------+----------+----------+
"""


def test_grid_tables_keep_numbering_and_headers(work: WorkFactory) -> None:
    completed_process, directory = work(make_grid_body(GRID_TABLE), lint=True)
    assert completed_process.returncode == 0, completed_process.stdout + completed_process.stderr
    with zipfile.ZipFile(directory / "out.docx") as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    assert_grid_document(root)


def test_grid_cell_spans_both_axes(built: BuiltFactory) -> None:
    source = (
        "<!-- #tbl:combined Объединение по двум осям -->\n\n"
        "+---+---+---+\n| А | Б | В |\n+===+===+===+\n"
        "| Блок  | 1 |\n|       +---+\n|       | 2 |\n+-------+---+\n"
    )
    root = ET.fromstring(built(source)["word/document.xml"])
    assert_grid_cell_spans(root)
