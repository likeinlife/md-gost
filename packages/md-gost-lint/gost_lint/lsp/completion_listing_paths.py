"""Complete a listing's file path using the language named on its fence."""

from collections.abc import Iterator
from pathlib import Path

from gost_lint.lsp.completion_files import file_names
from gost_lint.lsp.completion_types import Suggestion
from gost_lint.lsp.listing_attributes import FileAttribute, file_attribute
from gost_lint.lsp.path_matching import matching_names
from gost_lint.markdown import Document

# Pandoc language names and the common filename endings for their source files.
LANGUAGE_FILES = (
    (("python", "py", "python3"), (".py", ".pyi", ".pyw")),
    (("javascript", "js"), (".js", ".mjs", ".cjs", ".jsx")),
    (("typescript", "ts"), (".ts", ".tsx", ".mts", ".cts")),
    (("bash", "sh", "shell", "zsh"), (".sh", ".bash", ".zsh", ".ksh")),
    (("powershell",), (".ps1", ".psm1", ".psd1")),
    (("c",), (".c", ".h")),
    (("cpp", "c++"), (".cpp", ".hpp", ".cc", ".cxx", ".h", ".hh")),
    (("csharp", "cs"), (".cs",)),
    (("rust",), (".rs",)),
    (("ruby",), (".rb",)),
    (("kotlin",), (".kt", ".kts")),
    (("haskell",), (".hs", ".lhs")),
    (("markdown", "md"), (".md", ".markdown")),
    (("yaml", "yml"), (".yaml", ".yml")),
    (("html",), (".html", ".htm")),
    (("latex", "tex"), (".tex", ".sty", ".cls")),
)
SAME_EXTENSION = ("go", "java", "sql", "lua", "json", "xml", "css", "toml", "r", "http")


def _suffixes(classes: list[str]) -> frozenset[str] | None:
    for language in classes:
        for aliases, extensions in LANGUAGE_FILES:
            if language in aliases:
                return frozenset(extensions)
        if language in SAME_EXTENSION:
            return frozenset((f".{language}",))
    return None


def _candidates(
    prefix: str,
    root: Path,
    workspace_root: Path | None,
    classes: list[str],
) -> Iterator[str]:
    outside_book = "/" in prefix and ".." in Path(prefix).parts
    boundary = workspace_root if workspace_root and outside_book else root
    return file_names(prefix, root, boundary, image=False, suffixes=_suffixes(classes))


def _suggest(name: str, attribute: FileAttribute) -> Suggestion:
    ending = "" if name.endswith("/") else attribute.closing
    return Suggestion(
        name,
        "Файл листинга",
        name + ending,
        attribute.start,
        attribute.end,
        filter_text=name,
    )


def listing_path_suggestions(
    document: Document,
    root: Path,
    line: int,
    column: int,
    workspace_root: Path | None = None,
) -> list[Suggestion]:
    """Handle listing path suggestions."""
    found = file_attribute(document, line, column)
    if found is None:
        return []
    attribute, classes = found
    prefix = document.lines[line][attribute.start : column]
    names = _candidates(prefix, root, workspace_root, classes)
    return [
        _suggest(name, attribute)
        for name in matching_names(names, prefix)
        if attribute.quote not in name and "\n" not in name and "\r" not in name
    ]
