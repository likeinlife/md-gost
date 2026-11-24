"""Exercise completion edits against the Markdown that the editor would receive."""

from pathlib import Path

import pytest

from gost_lint.lsp.completion import Suggestion, complete
from gost_lint.lsp.completion_types import EditorOptions
from gost_lint.markdown import Document
from gost_lint.work import Work

CHAPTER = Path("/work/chapter.md")
DEFINITIONS = (
    "# Приложение А. Матрица {#appendix-acceptance .landscape}\n\n"
    "## Оценка результата\n\n"
    "<!-- #tbl:stack Технологический стек -->\n\n"
    "| Язык | Роль |\n| --- | --- |\n| Python | Основной |\n\n"
    "![Схема](diagram.png){#fig:view}\n\n"
    "<!-- #bib:book Автор учебника -->\n\n"
    "<!-- #bib:article Автор статьи -->\n\n"
    "<!-- #eq:sum -->\n\n$$\na+b\n$$\n\n"
    '```{.python #lst:source caption="Основной модуль"}\npass\n```\n'
)
CURSOR = "◊"
GROUP = "[@bib:book; "
MARKED = "marked"
TABLE = "tbl:stack"


def _work(chapter: Document) -> Work:
    other = Document.from_text(CHAPTER.with_name("definitions.md"), CHAPTER.parent, DEFINITIONS)
    documents = [chapter, other]
    return Work(CHAPTER.parent, None, [doc.rel for doc in documents], documents)


def choices(marked: str, *, snippets: bool = True) -> list[Suggestion]:
    before = marked.partition(CURSOR)[0]
    current = Document.from_text(CHAPTER, CHAPTER.parent, marked.replace(CURSOR, ""))
    line = before.count("\n")
    column = len(before.rsplit("\n", 1)[-1])
    return complete(current, _work(current), line, column, EditorOptions(snippets))


def apply(marked: str, choice: Suggestion) -> str:
    line = marked[: marked.index(CURSOR)].count("\n")
    lines = marked.replace(CURSOR, "").split("\n")
    previous = lines[line]
    prefix = previous[: choice.start]
    suffix = previous[choice.end :]
    lines[line] = f"{prefix}{choice.text}{suffix}"
    return "\n".join(lines)


def only_choice(marked: str, *, snippets: bool = True) -> Suggestion:
    candidates = choices(marked, snippets=snippets)
    assert len(candidates) == 1
    return candidates[0]


class TestReferences:
    def test_all_types_from_another_chapter(self) -> None:
        candidates = choices("См. [@◊")
        assert {choice.label for choice in candidates} == {
            TABLE,
            "bib:book",
            "bib:article",
            "eq:sum",
            "fig:view",
            "lst:source",
        }
        assert candidates[0].detail == "definitions.md — Технологический стек"

    @pytest.mark.parametrize(MARKED, ["😀 [@tbl:st◊", "😀 [@tbl:sta◊zz]", "😀 [@t◊bl:stack]"])
    def test_replace_token_once(self, marked: str) -> None:
        choice = only_choice(marked)
        assert choice.label == TABLE
        assert apply(marked, choice) == "😀 [@tbl:stack]"

    @pytest.mark.parametrize("prefix", ["", "@", "@bib:ar"])
    def test_bibliography_group(self, prefix: str) -> None:
        marked = f"{GROUP}{prefix}{CURSOR}]"
        candidates = choices(marked)
        assert all(choice.label.startswith("bib:") for choice in candidates)
        selected = next(choice for choice in candidates if choice.label == "bib:article")
        assert apply(marked, selected) == f"{GROUP}@bib:article]"

    def test_first_reference_in_group(self) -> None:
        marked = "[@b◊; @bib:article]"
        selected = next(choice for choice in choices(marked) if choice.label == "bib:book")
        assert apply(marked, selected) == f"{GROUP}@bib:article]"

    @pytest.mark.parametrize(
        MARKED,
        [
            "```python\n[@tbl:◊\n```",
            "`пример [@tbl:◊]`",
            "<!-- служебный [@tbl:◊] -->",
            "<!-- служебный\n[@tbl:◊",
            "$$\n[@tbl:◊\n$$",
            "Обычный текст @tbl:◊",
        ],
    )
    def test_excluded_context(self, marked: str) -> None:
        assert not choices(marked)


class TestSectionLinks:
    @pytest.mark.parametrize(
        MARKED,
        ["[см.](#app◊", "[см.](#app◊xxx)", "[см.](definitions.md#app◊)"],
    )
    def test_complete_target(self, marked: str) -> None:
        choice = only_choice(marked)
        prefix = marked.split("#", maxsplit=1)[0]
        expected = f"{prefix}#appendix-acceptance)"
        assert apply(marked, choice) == expected
        assert "Приложение А. Матрица" in choice.detail

    def test_suggest_explicit_and_generated_ids(self) -> None:
        candidates = choices("[в разделе](#◊)")
        assert {choice.label for choice in candidates} == {
            "appendix-acceptance",
            "оценка-результата",
        }

    @pytest.mark.parametrize(
        MARKED,
        [
            "`[см.](#app◊)`",
            "[см.](chapter.md#app◊)",
            "[см.](bad%00.md#app◊)",
            "[сайт](https://example.org/#app◊)",
        ],
    )
    def test_unavailable_targets(self, marked: str) -> None:
        assert not choices(marked)


class TestTables:
    def test_plain_template_is_valid(self) -> None:
        marked = "tbl◊"
        choice = only_choice(marked, snippets=False)
        text = apply(marked, choice)
        assert not choice.snippet
        assert choice.filter_text
        assert "tbl" in choice.filter_text.split()
        assert "$" not in text
        document = Document.from_text(CHAPTER, CHAPTER.parent, text)
        assert [block.kind for block in document.blocks] == ["table_marker", "table"]

    @pytest.mark.parametrize("prefix", ["", "|"])
    def test_row_uses_header_width(self, prefix: str) -> None:
        header = r"| Левый \| правый | Средний | Конец |"
        marked = f"{header}\n| --- | --- | --- |\n{prefix}{CURSOR}"
        choice = only_choice(marked)
        assert choice.snippet
        assert choice.text == "| ${1:Значение} | ${2:Значение} | ${3:Значение} |"
        plain = only_choice(marked, snippets=False)
        assert plain.text == "| Значение | Значение | Значение |"

    def test_template_key_is_available(self) -> None:
        marked = "<!-- #tbl:table Уже есть -->\n\n| A | B |\n| --- | --- |\n\n◊"
        choice = next(candidate for candidate in choices(marked) if candidate.label == "Таблица")
        assert "#tbl:${1:table-2}" in choice.text

    def test_existing_cell_is_preserved(self) -> None:
        assert not choices("| Первая | ◊Текст |")

    def test_grid_row_is_preserved(self) -> None:
        assert not choices("+-----+-----+\n| A   | B   |\n+=====+=====+\n|◊")
