"""Verify the Markdown left in the editor after inserting a figure, table or local link."""

from pathlib import Path

import pytest

from gost_lint.lsp.completion_markup import markup_suggestions
from gost_lint.lsp.completion_paths import path_suggestions
from gost_lint.lsp.completion_types import Suggestion
from gost_lint.markdown import Document

CURSOR = "◊"
FIGURE = "![Название рисунка](img/figure.png){#fig:figure-2}"
REFERENCE = "[Текст ссылки](адрес)"
NAME = "Мой рисунок.png"
ASSETS = "иллюстрации"
CHAPTER = "Глава два.md"
CAPTION = ' "Описание")'
MARKED = "marked"


def _edit(marked: str, choice: Suggestion) -> str:
    source = marked.replace(CURSOR, "")
    before = source[: choice.start]
    return before + choice.text + source[choice.end :]


def _document(path: Path, marked: str) -> Document:
    return Document.from_text(path, path.parent, marked.replace(CURSOR, ""))


def _markup(marked: str, *, snippets: bool = False) -> list[Suggestion]:
    chapter = _document(Path("chapter.md"), marked)
    figure = _document(Path("other.md"), "![Фото](a.jpg){#fig:figure}")
    return markup_suggestions(
        chapter,
        [chapter, figure],
        0,
        marked.index(CURSOR),
        snippets=snippets,
    )


class TestTemplates:
    def test_bibliography_template_uses_free_key(self) -> None:
        chapter = _document(Path("references.md"), "bib")
        other = _document(Path("intro.md"), "<!-- #bib:source Книга -->")
        choices = markup_suggestions(chapter, [chapter, other], 0, 3, snippets=True)
        assert choices[0].text == "<!-- #bib:${1:source-2} ${2:Описание источника} -->"
        plain = _markup("bib◊")[0]
        assert _edit("bib◊", plain) == "<!-- #bib:source Описание источника -->"

    @pytest.mark.parametrize(MARKED, ["!◊", "img◊", "![◊]", "рис◊"])
    def test_insert_image(self, marked: str) -> None:
        choice = _markup(marked)[0]
        assert _edit(marked, choice) == FIGURE
        assert not choice.snippet

    @pytest.mark.parametrize(MARKED, ["link◊", "См. [◊] далее"])
    def test_insert_link(self, marked: str) -> None:
        choice = _markup(marked)[0]
        assert REFERENCE in _edit(marked, choice)
        if marked.endswith("далее"):
            assert _edit(marked, choice) == f"См. {REFERENCE} далее"

    def test_formula_template_is_a_display_formula(self) -> None:
        choice = _markup("формула◊")[0]
        rendered = "<!-- #eq:formula -->\n\n$$E = mc^{2}$$\n\nгде $E$ — пояснение."
        assert choice.text == rendered
        document = _document(Path("chapter.md"), choice.text)
        kinds = [block.kind for block in document.blocks]
        assert kinds[:3] == ["eq_marker", "formula", "paragraph"]

    def test_formula_snippet_escapes_dollars_for_zed(self) -> None:
        choice = _markup("формула◊", snippets=True)[0]
        assert choice.snippet
        assert r"\$\$" in choice.text
        literal = choice.text.replace(r"\$", "")
        assert "$$" not in literal
        assert "${1:" in literal
        assert "${4:" in literal

    def test_grid_template_is_valid(self) -> None:
        choice = _markup("grid◊")[0]
        grid_doc = _document(Path("chapter.md"), choice.text)
        assert [block.kind for block in grid_doc.blocks] == ["table_marker", "table"]
        grid = grid_doc.blocks[-1].meta["grid"]
        assert not grid.errors
        assert "${1:" in _markup("+◊", snippets=True)[0].text


class Book:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.folder = root / "chapters"
        self.folder.mkdir()
        self.chapter = self.folder / "intro.md"
        self.other = _document(root / CHAPTER, "# Глава")
        assets = root / ASSETS
        assets.mkdir()
        for name in (NAME, "схема.puml", "архитектура.idef0", "график.py", "notes.txt"):
            (assets / name).touch()

    def paths(self, marked: str) -> dict[str, Suggestion]:
        document = _document(self.chapter, marked)
        book = [document, self.other]
        choices = path_suggestions(document, book, self.root, 0, marked.index(CURSOR))
        return {choice.label: choice for choice in choices}


@pytest.fixture
def book(tmp_path: Path) -> Book:
    return Book(tmp_path.resolve())


class TestPathSuggestions:
    def test_browse_image_folder(self, book: Book) -> None:
        marked = "![Снимок](◊)"
        folder = f"{ASSETS}/"
        assert _edit(marked, book.paths(marked)[folder]) == f"![Снимок]({folder})"
        inner = f"![Снимок]({folder}{CURSOR})"
        choices = book.paths(inner)
        assert set(choices) == {
            folder + name for name in (NAME, "схема.puml", "архитектура.idef0", "график.py")
        }
        edited = _edit(inner, choices[folder + NAME])
        assert edited == f"![Снимок]({folder}{NAME})"

    def test_chapter_with_spaces_uses_relative_url(self, book: Book) -> None:
        marked = f"См. [пример](../Гл◊xxx.md{CAPTION}"
        choice = book.paths(marked)[f"../{CHAPTER}"]
        assert _edit(marked, choice) == f"См. [пример](../Глава%20два.md{CAPTION}"
        marked = "См. [пример](◊"
        choice = book.paths(marked)[f"../{CHAPTER}"]
        edited = _edit(marked, choice)
        assert edited.endswith("%20два.md)")

    @pytest.mark.parametrize(
        MARKED,
        ["[см.](https://◊)", "[см.](#◊)", "`![Снимок](◊)`", r"\[см.](◊)"],
    )
    def test_ignore_non_local_or_literal_path(self, book: Book, marked: str) -> None:
        assert not book.paths(marked)

    def test_skip_external_paths_and_cache(self, book: Book) -> None:
        (book.root / "external").symlink_to(book.root.parent)
        cache = book.root / ".md-to-gost"
        cache.mkdir()
        (cache / "generated.png").touch()
        assert not book.paths("![Фото](../◊)")
        assert not book.paths("![Фото](external/◊)")
        assert not book.paths("![Фото](.md-to-gost/◊)")
