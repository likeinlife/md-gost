"""Merged cells, source locations and the existing table rules share one contract."""

from pathlib import Path

import pytest
from conftest import rules_found, run_lint

from gost_lint.fixes import autofix
from gost_lint.markdown.grid import Grid, GridCell, parse_grid
from gost_lint.markdown.parser import parse as parse_document

NO_CONFIG = "--no-config"
GRID_FILE = "grid.md"
BODY_LINE = 14
TABLE_KIND = "table"


def _cell_layout(cells: list[GridCell]) -> list[tuple[str, int, int]]:
    return [(cell.text, cell.rowspan, cell.colspan) for cell in cells]


@pytest.fixture
def source(fixtures: Path) -> str:
    return (fixtures / GRID_FILE).read_text(encoding="utf-8")


class TestGroup1:
    def test_grid_is_one_table_with_its_source_span(self, source: str) -> None:
        blocks = parse_document(source)
        assert [block.kind for block in blocks] == [
            "heading",
            "heading",
            "paragraph",
            "table_marker",
            "table",
            "paragraph",
        ]
        table = blocks[4]
        assert (table.start, table.end) == (9, 17)
        grid: Grid = table.meta["grid"]
        assert not grid.errors
        columns = 4
        header_offset = 4
        assert grid.columns == columns
        assert grid.header_offset == header_offset

    def test_grid_header_spans(self, source: str) -> None:
        table = next(block for block in parse_document(source) if block.kind == TABLE_KIND)
        grid: Grid = table.meta["grid"]
        spans = {cell.text: (cell.rowspan, cell.colspan) for cell in grid.cells}
        assert spans["Этап"] == (2, 1)
        assert spans["Показатель"] == (2, 1)
        assert spans["Значение"] == (1, 2)
        assert spans["Анализ"] == (2, 1)

    def test_fix_preserves_the_entire_mesh(self, source: str) -> None:
        assert autofix(source) == source

    @pytest.mark.parametrize("indent", ["", " ", "   "])
    def test_indented_mesh(self, indent: str, source: str) -> None:
        table = next(block for block in parse_document(source) if block.kind == TABLE_KIND)
        assert not parse_grid([indent + line for line in table.lines]).errors

    @pytest.mark.parametrize(
        "table",
        [
            "+---+---+\n| А | Б |\n+===+===+\n| 1 | 2 |",  # unclosed
            "+---+---+\n| А | Б |\n+---+---+\n| 1 | 2 |\n+---+---+",  # no header
            "+---+---+\n| А | Б |\n+===+---+\n| 1 | 2 |\n+---+---+",  # partial header
            "+---+---+\n| А | Б |\n+===+===+\n+---+---+",  # no content
            (
                "+---+---+\n| А | Б |\n+===+===+\n| 1 | 2 |\n|   +---+\n|       |\n+---+---+"
            ),  # L shape
        ],
    )
    def test_broken_mesh_is_reported(self, table: str) -> None:
        assert parse_grid(table.splitlines()).errors

    def test_cell_can_span_both_axes(
        self,
    ) -> None:
        table = (
            "+---+---+---+\n| А | Б | В |\n+===+===+===+\n"
            "|       | 1 |\n|       +---+\n|       | 2 |\n+-------+---+"
        )
        grid = parse_grid(table.splitlines())
        assert not grid.errors
        square_span = 2
        assert any(cell.rowspan == cell.colspan == square_span for cell in grid.cells)

    def test_three_header_rows_and_multiline_text(
        self,
    ) -> None:
        table = (
            "+-----+-----------+\n| А   | Б         |\n|     +-----+-----+\n"
            "|     | В   | Г   |\n|     |     +-----+\n|     |     | Д   |\n"
            "+=====+=====+=====+\n| Одна      | 3   |\n| фраза     |     |\n"
            "+-----------+-----+"
        )
        grid = parse_grid(table.splitlines())
        assert not grid.errors
        header_cells = _cell_layout(grid.cells[:5])
        expected = [
            ("А", 3, 1),
            ("Б", 1, 2),
            ("В", 2, 1),
            ("Г", 1, 1),
            ("Д", 1, 1),
        ]
        assert header_cells == expected
        assert grid.cells[5].text == "Одна фраза"
        colspan = 2
        assert grid.cells[5].colspan == colspan


class TestGroup2:
    def test_empty_cell_does_not_merge_columns(
        self,
    ) -> None:
        table = "+---+---+\n| А | Б |\n+===+===+\n|   | 2 |\n+---+---+"
        grid = parse_grid(table.splitlines())
        assert not grid.errors
        cells = [(cell.text, cell.colspan) for cell in grid.cells[2:]]
        assert cells == [("", 1), ("2", 1)]

    def test_existing_rules_apply_to_grid(self, sandbox: Path, source: str) -> None:
        target = sandbox / GRID_FILE
        target.write_text(source.replace("<!-- #tbl:plan План и факт по этапам -->", ""))
        assert {"REF001", "REF003"} <= rules_found(target, NO_CONFIG)
        target.write_text(source.split("План интервью", maxsplit=1)[0])
        assert "STRUCT001" in rules_found(target, NO_CONFIG)
        target.write_text(
            source.replace("\n\n+--------------+", "\n\nАбзац.\n\n+--------------+", 1),
        )
        assert "REF002" in rules_found(target, NO_CONFIG)

    def test_bold_allowed_in_all_header_rows_only(self, sandbox: Path, source: str) -> None:
        target = sandbox / GRID_FILE
        target.write_text(source.replace("План     ", "**План** "))
        assert rules_found(target, NO_CONFIG) == set()
        target.write_text(source.replace("Интервью         ", "**Интервью**     "))
        assert "STYLE001" in rules_found(target, NO_CONFIG)

    def test_numbering_rule_applies_to_body_cells(self, sandbox: Path, source: str) -> None:
        target = sandbox / GRID_FILE
        target.write_text(
            source.replace("Интервью         ", "1. Интервью      ").replace(
                "Требования       ",
                "2. Требования    ",
            ),
        )
        _, issues = run_lint(target, NO_CONFIG)
        assert {issue["rule"] for issue in issues} == {"STYLE006"}
        assert issues[0]["line"] == BODY_LINE

    def test_code_fence_protects_grid(self, source: str) -> None:
        markdown = f"```markdown\n{source}\n```\n"
        assert [block.kind for block in parse_document(markdown)] == ["code"]
