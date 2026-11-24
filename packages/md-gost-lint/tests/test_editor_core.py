"""Regression cases for ranges and partially written editor buffers."""

from pathlib import Path

import pytest
from conftest import run_lint

from gost_lint.markdown import Document
from gost_lint.markdown.metadata import table_rows


def _document(text: str) -> Document:
    return Document.from_text(Path("book/chapter.md"), Path("book"), text)


def test_group_keys_have_individual_source_ranges() -> None:
    line = "📖 См. [@bib:один; @bib:два]."
    doc = _document(f"# Работа\r\n\r\n{line}")
    assert doc.rel == "chapter.md"
    spans = list(doc.reference_spans())
    assert [span.label for span in spans] == ["bib:один", "bib:два"]
    citation_line = 2
    for span in spans:
        assert span.line == citation_line
        assert line[span.start : span.end] == span.label


def test_keys_in_captions_are_not_declarations() -> None:
    source = (
        '![#fig:пример](a.png){caption="#fig:иной" #fig:пример}\n\n'
        '  ```{.python caption="#lst:пример" #lst:пример}\npass\n   ````\n\n'
        "<!-- #bib:источник Название -->\n"
    )
    doc = _document(source)
    definitions = list(doc.definition_spans())
    assert [span.line for span, _ in definitions] == [0, 2, 6]
    for span, _ in definitions:
        line = doc.lines[span.line]
        assert span.start == line.rindex(span.label)
        assert line[span.start : span.end] == span.label


class TestLiteralContexts:
    @pytest.mark.parametrize("unclosed", ["<!--", "<!-- #tbl:", "<!--\n# скрылось", "<!--\n"])
    def test_unclosed_comment_parses_to_end(self, unclosed: str) -> None:
        doc = _document(unclosed)
        line = unclosed.count("\n")
        column = len(unclosed.rsplit("\n", maxsplit=1)[-1])
        assert [block.kind for block in doc.blocks] == ["comment"]
        assert not doc.is_prose_position(line, column)

    def test_protected_content_is_not_indexed(self) -> None:
        source = (
            "В ``коде ` [@fig:код]``.\n\n"
            "<!--\n[@fig:скрыто]\n-->\n\n"
            "```plantuml\n[@fig:тело]\n````\n"
            "$$\n[@eq:формула]\n$$\n\n"
            "| См. [@tbl:пример] |\n"
        )
        doc = _document(source)
        assert [span.label for span in doc.reference_spans()] == ["tbl:пример"]

    @pytest.mark.parametrize("opening", ["```python", "~~~", "$$"])
    def test_open_block_protects_final_newline(self, opening: str) -> None:
        doc = _document(f"{opening}\n")
        assert not doc.is_prose_position(1, 0)

    def test_inline_comment_has_visible_suffix(self) -> None:
        doc = _document("Текст <!--\n[@tbl:нет] --> [@tbl:да]\n")
        assert [span.label for span in doc.reference_spans()] == ["tbl:да"]
        assert doc.is_prose_position(2, 0)


def test_local_duplicate_points_to_second_key(sandbox: Path) -> None:
    marker = "<!-- #eq:пример -->"
    chapter = sandbox / "twice.md"
    chapter.write_text(f"{marker}\n\n{marker}\n", encoding="utf-8")
    _, issues = run_lint(chapter, "--no-config", "--rules", "REF004")
    locations = [(issue["line"], issue["column"]) for issue in issues]
    assert locations == [(3, marker.index("eq:") + 1)]


def test_pipe_rows_keep_escaped_and_empty_cells() -> None:
    assert table_rows([r"| A\|B | C |", r"| A\\| B ||"]) == [
        [r"A\|B", "C"],
        [r"A\\", "B", ""],
    ]
