"""Completions for heading attributes such as `.page` and `{-}`."""

from pathlib import Path

import pytest

from gost_lint.lsp.completion import complete
from gost_lint.lsp.completion_types import EditorOptions, Suggestion
from gost_lint.markdown import Document
from gost_lint.work import Work

CHAPTER = Path("/work/chapter.md")
CURSOR = "◊"
PAGE = ".page"
LANDSCAPE = ".landscape"
PAPER = "paper=a3"
PAGE_LINE = "# Заключение {.page}"
OPEN = "# Заключение {◊"


def _choices(marked: str) -> list[Suggestion]:
    before = marked.partition(CURSOR)[0]
    current = Document.from_text(CHAPTER, CHAPTER.parent, marked.replace(CURSOR, ""))
    line = before.count("\n")
    column = len(before.rsplit("\n", 1)[-1])
    book = Work(CHAPTER.parent, None, [current.rel], [current])
    return complete(current, book, line, column, EditorOptions(snippets=False))


def _named(marked: str, label: str) -> Suggestion:
    found = [choice for choice in _choices(marked) if choice.label == label]
    assert len(found) == 1
    return found[0]


def _apply(marked: str, label: str) -> str:
    choice = _named(marked, label)
    lines = marked.replace(CURSOR, "").split("\n")
    index = marked.partition(CURSOR)[0].count("\n")
    lines[index] = _splice(lines[index], choice)
    return "\n".join(lines)


def _splice(previous: str, choice: Suggestion) -> str:
    prefix = previous[: choice.start]
    suffix = previous[choice.end :]
    return f"{prefix}{choice.text}{suffix}"


class TestHeadingAttributes:
    def test_open_brace_lists_properties(self) -> None:
        choices = _choices(OPEN)
        assert {choice.label for choice in choices} == {
            "-",
            ".unnumbered",
            PAGE,
            LANDSCAPE,
            PAPER,
        }
        selected = _named(OPEN, PAGE)
        assert selected.detail == "с новой страницы"

    @pytest.mark.parametrize(
        ("marked", "label", "expected"),
        [
            (OPEN, "-", "# Заключение {-}"),
            (OPEN, PAGE, PAGE_LINE),
            ("# Заключение {.pa◊", PAGE, PAGE_LINE),
            ("# Заключение {.pa◊ge}", PAGE, PAGE_LINE),
            ("# Заключение {page◊", PAGE, PAGE_LINE),
            ("# Заключение {- .◊", PAGE, "# Заключение {- .page}"),
            ("# Заключение {.page ◊}", LANDSCAPE, "# Заключение {.page .landscape}"),
            ("## Подраздел {paper◊", PAPER, "## Подраздел {paper=a3}"),
            ("# Приложение {#id .la◊", LANDSCAPE, "# Приложение {#id .landscape}"),
            ("# Заключение {◊.page}", LANDSCAPE, "# Заключение {.landscape .page}"),
        ],
    )
    def test_inserts_attribute(self, marked: str, label: str, expected: str) -> None:
        assert _apply(marked, label) == expected

    def test_dot_prefix_filters_classes(self) -> None:
        labels = {choice.label for choice in _choices("# Заключение {.◊")}
        assert labels == {".unnumbered", PAGE, LANDSCAPE}

    def test_typed_class_sets_filter_text(self) -> None:
        choice = _named("# Заключение {pa◊", PAGE)
        assert choice.filter_text == "page"

    def test_skips_properties_already_present(self) -> None:
        marked = "# А {- .unnumbered .page ◊ paper=a3}"
        labels = {choice.label for choice in _choices(marked)}
        assert labels == {LANDSCAPE}
        filled = "# А {- .unnumbered .page .landscape paper=a3}"
        assert _apply(marked, LANDSCAPE) == filled

    @pytest.mark.parametrize(
        "marked",
        [
            "Текст {.pa◊",
            "```\n# Title {.pa◊\n```",
            "# Заключение {.page} ◊",
            "# Заключение {#ident◊}",
        ],
    )
    def test_unavailable(self, marked: str) -> None:
        labels = {choice.label for choice in _choices(marked)}
        assert PAGE not in labels
