"""Language names from the installed Pandoc, the work, and built-in renderers."""

import re
from collections.abc import Iterator
from functools import cache

from gost_lint.markdown import Block, Document
from gost_lint.markdown.fences import FIGURE_CLASSES
from gost_lint.markdown.metadata import QUOTED_ATTRIBUTE
from gost_lint.markdown.syntax import FENCE

LANGUAGES = (
    "bash",
    "c",
    "cpp",
    "csharp",
    "css",
    "go",
    "html",
    "http",
    "java",
    "javascript",
    "json",
    "kotlin",
    "lua",
    "markdown",
    "powershell",
    "python",
    "r",
    "ruby",
    "rust",
    "sh",
    "sql",
    "text",
    "toml",
    "typescript",
    "xml",
    "yaml",
)
BLOCK_KINDS = ("code", "listing", "diagram")
BOOK_LANGUAGE = re.compile(r"(?:^|[\s{]\.)([\w][\w+#-]*)(?=\s|}|$)")


@cache
def pandoc_languages() -> frozenset[str]:
    """Handle pandoc languages."""
    try:
        import pypandoc
    except ImportError:
        return frozenset()
    try:
        listing = pypandoc.convert_text(
            "",
            to="plain",
            format="markdown",
            extra_args=["--list-highlight-languages"],
            verify_format=False,
        )
    except (OSError, RuntimeError):
        return frozenset()
    return frozenset(listing.splitlines())


def language_names(
    documents: list[Document],
    editing: Block,
    installed: frozenset[str],
) -> list[str]:
    """Handle language names."""
    languages = set(LANGUAGES).union(installed)
    languages.update(name[1:] for name in FIGURE_CLASSES)
    languages.update(_book_languages(documents, editing))
    return sorted(languages)


def _book_languages(documents: list[Document], editing: Block) -> Iterator[str]:
    for document in documents:
        for block in document.of_kind(*BLOCK_KINDS):
            if block is not editing:
                yield from _declared_language(block)


def _declared_language(block: Block) -> Iterator[str]:
    fence = FENCE.match(block.lines[0])
    if fence is None:
        message = "fence line does not match"
        raise ValueError(message)
    unquoted = QUOTED_ATTRIBUTE.sub("", fence["info"].strip())
    match = BOOK_LANGUAGE.search(unquoted)
    if match is not None:
        yield match[1]
