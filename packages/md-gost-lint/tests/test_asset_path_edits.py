"""Check the names offered and the source text left after accepting a file completion."""

from pathlib import Path

import pytest

from gost_lint.lsp.completion_listing_paths import listing_path_suggestions
from gost_lint.lsp.completion_paths import path_suggestions
from gost_lint.lsp.completion_types import Suggestion
from gost_lint.markdown import Document
from gost_lint.rules.attachments import listing_range_without_file

CURSOR = "◊"
PYTHON = "scripts/plots/Мой отчёт.py"
CHART = "figures/plots/Мой план.PNG"
PY_HEADER = '```{.python #lst:demo file="'
END_ATTRS = '" caption="Пример" lines="1-2"}'
MARKED = "marked"


class Files:
    def __init__(self, root: Path) -> None:
        self.root = root / "book"
        self.workspace = root
        for name in (PYTHON, CHART, "scripts/plots/part.sql", "chapter.md"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

    def choices(self, marked: str) -> dict[str, Suggestion]:
        chapter = Document.from_text(
            self.root / "chapter.md",
            self.root,
            marked.replace(CURSOR, ""),
        )
        before = marked.partition(CURSOR)[0].split("\n")
        point = len(before) - 1, len(before[-1])
        if marked.startswith(("`", "~", "<")):
            choices = listing_path_suggestions(chapter, self.root, *point, self.workspace)
        else:
            choices = path_suggestions(chapter, [chapter], self.root, *point)
        return {choice.label: choice for choice in choices}

    def apply(self, marked: str, name: str) -> str:
        choice = self.choices(marked)[name]
        source = marked.replace(CURSOR, "")
        prefix = source[: choice.start]
        return prefix + choice.text + source[choice.end :]


@pytest.fixture
def files(tmp_path: Path) -> Files:
    return Files(tmp_path.resolve())


class TestListing:
    @pytest.mark.parametrize("prefix", ["", "мой", ".py", "scripts/plots/Мо"])
    def test_selected_source(self, files: Files, prefix: str) -> None:
        marked = f"{PY_HEADER}{prefix}{CURSOR}old.py{END_ATTRS}"
        options = files.choices(marked)
        assert PYTHON in options
        sources = {name for name in options if not name.endswith("/")}
        assert sources == {PYTHON}
        assert files.apply(marked, PYTHON) == PY_HEADER + PYTHON + END_ATTRS

    @pytest.mark.parametrize("quote", ['"', "'"])
    def test_language_after_file(self, files: Files, quote: str) -> None:
        marked = f"~~~{{file={quote}{CURSOR}{quote} .sql}}"
        assert "scripts/plots/part.sql" in files.choices(marked)
        assert PYTHON not in files.choices(marked)

    @pytest.mark.parametrize("quote", ['"', "'"])
    def test_completed_file_in_linter(self, files: Files, quote: str) -> None:
        caption = 'Пример file="другой.py"'
        attrs = f".python #lst:demo caption='{caption}' file='◊' lines={quote}1-2{quote}"
        filled = files.apply(f"~~~{{{attrs}}}", PYTHON)
        chapter = Document.from_text(files.root / "chapter.md", files.root, f"{filled}\n~~~")
        listing = chapter.of_kind("listing")[0]
        assert listing.meta["src"] == PYTHON
        assert listing.meta["caption"] == caption
        assert listing.meta["lines"] == "1-2"
        assert not list(listing_range_without_file(chapter))

    @pytest.mark.parametrize("end", ["", "}"])
    def test_finish_attribute(self, files: Files, end: str) -> None:
        marked = PY_HEADER + CURSOR + end
        assert files.apply(marked, PYTHON) == f'{PY_HEADER}{PYTHON}"}}'

    def test_parent_path_within_workspace(self, files: Files) -> None:
        path = files.workspace / "examples" / "code.py"
        path.parent.mkdir()
        path.touch()
        assert "../examples/code.py" in files.choices(f"{PY_HEADER}../examples/c◊")
        assert not files.choices(f"{PY_HEADER}../../◊")

    @pytest.mark.parametrize(
        MARKED,
        [
            f"~~~python\n{PY_HEADER}{CURSOR}",
            "```{.python caption='test file=\"◊\"'}",
            f"<!--\n{PY_HEADER}{CURSOR}",
            '```{.plot file="◊"}',
            '~ literal file="◊"',
            '```{.python} file="◊"',
        ],
    )
    def test_non_listing_context(self, files: Files, marked: str) -> None:
        assert not files.choices(marked)


class TestMarkdown:
    @pytest.mark.parametrize("prefix", ["", "мой", ".png"])
    def test_find_nested_figure(self, files: Files, prefix: str) -> None:
        marked = f"![Итоги]({prefix}{CURSOR}old.png){{#fig:plot}}"
        assert files.apply(marked, CHART) == f"![Итоги]({CHART}){{#fig:plot}}"

    def test_deep_link_by_filename(self, files: Files) -> None:
        marked = "[Программа](Мой◊)"
        expected = PYTHON.replace(" ", "%20")
        assert files.apply(marked, PYTHON) == f"[Программа]({expected})"
