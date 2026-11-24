"""Formatting must preserve table cells, Markdown and the widths Pandoc renders."""

import pytest

from gost_lint.markdown.format_tables import format_table
from gost_lint.markdown.grid import parse_grid
from gost_lint.markdown.parser import parse as parse_document
from gost_lint.markdown.table_widths import text_width

SOURCE = "source"
ESCAPED_PIPE = r"x\|y"
BORDERLINE = 68
WIDE_TEXT = "Показатель, по которому рассчитывается длительность каждого этапа выполнения работ"
SIMPLE = "Монета|Курс\n:---|---:\n€ | 1"


def _format(source: str) -> str:
    blocks = parse_document(source)
    assert len(blocks) == 1
    block = blocks[0]
    assert block.kind == "table"
    rewritten = "\n".join(format_table(block))
    finished = parse_document(rewritten)[0]
    assert format_table(finished) == finished.lines
    return rewritten


class TestPipeTable:
    def test_outer_pipes_and_column_alignment(self) -> None:
        formatted = _format(SIMPLE)
        assert formatted == "| Монета | Курс |\n| :---   | ---: |\n| €      | 1    |"

    def test_code_escapes_and_unicode(self) -> None:
        source = f"| X | Б |\n|--|:--:|\n|哈 | ``а`|б`` |\n|и\u0306 | {ESCAPED_PIPE} |"
        lines = _format(source).splitlines()
        assert len(set(map(text_width, lines))) == 1
        assert lines[-2].endswith("``а`|б`` |")
        assert ESCAPED_PIPE in lines[-1]
        assert "и\u0306" in lines[-1]

    def test_preserve_relative_dash_counts_when_wide(self) -> None:
        source = f"| Категория| Б|\n|:-|------------:|\n|{WIDE_TEXT}|2|"
        formatted = _format(source)
        divider = formatted.splitlines()[1]
        markers = divider.strip("|").split("|")
        assert list(map(str.strip, markers)) == [":-", "------------:"]

    def test_indented_width_threshold(self) -> None:
        field = "д" * BORDERLINE
        source = f"   А |Б\n   --|---\n   {field}|б"
        assert _format(source) == source

    @pytest.mark.parametrize(
        SOURCE,
        ["| А | Б |\n| всего | 2 |", "|А|Б|\n|--|--|\n|одна|", "|А|Б|\n|--|--|\n| $x|y$ | 2 |"],
    )
    def test_leave_ambiguous_rows(self, source: str) -> None:
        assert _format(source) == source


class TestGridTable:
    def test_russian_merged_header_and_multiline_body(self) -> None:
        source = (
            "+-----+---------+\n|  А  |Группа   |\n|     +----+----+\n|     | Б  | В  |\n"
            "+=====+====+====+\n|одна |  1 | 2  |\n|фраза|    |    |\n+-----+----+----+"
        )
        formatted = _format(source)
        assert "| А   | Группа  |" in formatted
        assert "|одна | 1  | 2  |\n|фраза|" in formatted
        assert parse_grid(formatted.splitlines()) == parse_grid(source.splitlines())

    @pytest.mark.parametrize(
        SOURCE,
        [
            "+----+----+\n|А|Б|\n+====+====+\n| 1  | 2  |\n+----+----+",
            "+----------+\n|     code |\n+==========+\n| a        |\n+----------+",
        ],
    )
    def test_preserve_broken_mesh_and_indented_code(self, source: str) -> None:
        assert _format(source) == source


def test_pipe_in_prose_and_fenced_example() -> None:
    source = f"А | Б\nВ | Г\n\n```markdown\n{SIMPLE}\n```"
    assert [block.kind for block in parse_document(source)] == ["paragraph", "code"]


def test_prose_with_literal_pipe_after_table() -> None:
    source = f"{SIMPLE}\nТекст с `|` продолжается."
    assert [block.kind for block in parse_document(source)] == ["table", "paragraph"]
