"""Fence openers, language edits and buildable block completions."""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest

from gost_lint.lsp.completion import complete
from gost_lint.lsp.completion_types import EditorOptions, Suggestion
from gost_lint.lsp.fence_languages import pandoc_languages
from gost_lint.markdown import Document
from gost_lint.work import Work

CHAPTER = Path("/work/main.md")
MARKER = "◊"
LANGUAGE = "python"
LISTING = "Листинг кода"
EXISTING = '~~~{#lst:listing caption="Расчёт .incorrect" .projectdsl}\nsolve()\n~~~'


def _work(chapter: Document) -> Work:
    other = Document.from_text(CHAPTER.with_name("annex.md"), CHAPTER.parent, EXISTING)
    documents = [chapter, other]
    return Work(CHAPTER.parent, None, [doc.rel for doc in documents], documents)


def _choices(marked: str, *, snippets: bool = False) -> dict[str, Suggestion]:
    lines = marked.partition(MARKER)[0].split("\n")
    active = Document.from_text(CHAPTER, CHAPTER.parent, marked.replace(MARKER, ""))
    cursor = len(lines) - 1, len(lines[-1])
    choices = complete(active, _work(active), *cursor, EditorOptions(snippets))
    return {choice.label: choice for choice in choices}


@pytest.mark.parametrize(
    ("marked", "expected"),
    [
        ("```py◊", "```python"),
        ("~~~py◊th", "~~~python"),
        ("   ````{.py◊}", "   ````{.python}"),
        ("```{py◊", "```{.python}"),
        ('```{.py◊tt #lst:id caption="Модуль"}', '```{.python #lst:id caption="Модуль"}'),
        ('~~~{caption="С пробелом" #lst:id .py◊}', '~~~{caption="С пробелом" #lst:id .python}'),
    ],
)
def test_language_edit_preserves_attributes(marked: str, expected: str) -> None:
    options = _choices(marked)
    assert LANGUAGE in options
    assert "py" not in options
    choice = options[LANGUAGE]
    original = marked.replace(MARKER, "")
    suffix = original[choice.end :]
    assert original[: choice.start] + choice.text + suffix == expected


def test_work_languages_and_renderers() -> None:
    options = _choices("```◊")
    assert {LANGUAGE, "sql", "plantuml", "plot", "idef0", "projectdsl"} <= options.keys()
    assert "incorrect" not in options


@pytest.mark.parametrize(
    "marked",
    [
        "````markdown\n```py◊\n````",
        "~~~python\n~~~◊",
        "<!--\n```py◊\n-->",
        '```{.python caption=".py◊"}',
        "```{.python #lst:py◊}",
        "```text\ncode◊\n```",
        "Вставьте code◊",
    ],
)
def test_excluded_positions(marked: str) -> None:
    assert not _choices(marked)


class TestBlockTemplates:
    @pytest.mark.parametrize(
        ("word", "label", "kind"),
        [
            ("код", "Блок кода", "code"),
            ("lst", LISTING, "listing"),
            ("plantuml", "Диаграмма PlantUML", "diagram"),
            ("plot", "График Python", "diagram"),
            ("idef0", "Диаграмма IDEF0", "diagram"),
        ],
    )
    def test_plain_block_template(self, word: str, label: str, kind: str) -> None:
        choice = _choices(word + MARKER)[label]
        assert not choice.snippet
        assert (choice.start, choice.end) == (0, len(word))
        assert "${" not in choice.text
        document = Document.from_text(CHAPTER, CHAPTER.parent, choice.text)
        assert [block.kind for block in document.blocks] == [kind]

    def test_unique_listing_snippet(self) -> None:
        choice = _choices("листинг◊", snippets=True)[LISTING]
        assert choice.snippet
        assert "${1:python}" in choice.text
        assert "#lst:${2:listing-2}" in choice.text
        assert "${" not in choice.detail
        assert choice.filter_text == _choices(MARKER)[LISTING].filter_text


class TestPandocLanguages:
    @pytest.fixture(autouse=True)
    def uncached(self) -> Iterator[None]:
        pandoc_languages.cache_clear()
        yield
        pandoc_languages.cache_clear()

    def test_cache_installed_languages(self) -> None:
        with patch("pypandoc.convert_text", return_value="dockerfile\nfreshlang\n") as probe:
            names = pandoc_languages()
            assert names == {"dockerfile", "freshlang"}
            assert pandoc_languages() == names
            probe.assert_called_once_with(
                "",
                to="plain",
                format="markdown",
                extra_args=["--list-highlight-languages"],
                verify_format=False,
            )

    @pytest.mark.parametrize("error", [OSError("missing pandoc"), RuntimeError("pandoc failed")])
    def test_fallback(self, error: Exception) -> None:
        with patch("pypandoc.convert_text", side_effect=error):
            assert not pandoc_languages()
