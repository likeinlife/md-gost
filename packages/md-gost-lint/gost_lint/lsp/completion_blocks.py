"""Offer languages on an opening fence and full code blocks in prose."""

import re
from collections.abc import Iterator
from dataclasses import dataclass

from gost_lint.lsp.completion_types import Suggestion
from gost_lint.lsp.fence_languages import BLOCK_KINDS, language_names
from gost_lint.markdown import Block, Document
from gost_lint.markdown.syntax import FENCE

WORD = r"[\w+#-]*"
ATTRIBUTE = r"[^{}\s\"']+(?:\"[^\"\n]*\"|'[^'\n]*')?"
ATTRIBUTE_CLASS = rf"(?P<brace>\{{)\s*(?:(?:{ATTRIBUTE}\s+)*(?P<dot>\.))?"
LANGUAGE_AT_CURSOR = re.compile(rf"\s*(?:{ATTRIBUTE_CLASS})?(?P<language>{WORD})$")
LANGUAGE_TAIL = re.compile(WORD)
WORD_EDGE = re.compile(r"[\w+#}\s-]|$")


@dataclass(frozen=True)
class LanguageEdit:
    """Represent Language Edit."""

    prefix: str
    start: int
    end: int
    dotted: bool
    closing: str

    def choices(self, languages: list[str]) -> Iterator[Suggestion]:
        """Handle choices."""
        for name in languages:
            if name.casefold().startswith(self.prefix.casefold()):
                dot = "." if self.dotted else ""
                insertion = f"{dot}{name}{self.closing}"
                yield Suggestion(name, "Язык блока", insertion, self.start, self.end)


def _language_edit(fence: re.Match[str], column: int) -> LanguageEdit | None:
    offset = fence.end("fence")
    if column < offset or WORD_EDGE.match(fence.string, column) is None:
        return None
    token = LANGUAGE_AT_CURSOR.fullmatch(fence.string, offset, column)
    if token is None:
        return None
    tail = LANGUAGE_TAIL.match(fence.string, column)
    if tail is None:
        message = "language token has no tail"
        raise ValueError(message)
    return _edit(token, tail.end())


def _edit(token: re.Match[str], end: int) -> LanguageEdit:
    following = token.string[end:].strip()
    braces = bool(token["brace"])
    closing = "}" if braces and not following else ""
    dotted = braces and not token["dot"]
    return LanguageEdit(token["language"], token.start("language"), end, dotted, closing)


def _opening_at(document: Document, line: int) -> Block | None:
    blocks = document.of_kind(*BLOCK_KINDS)
    return next((block for block in blocks if block.start == line + 1), None)


def block_suggestions(
    document: Document,
    documents: list[Document],
    line: int,
    column: int,
    installed: frozenset[str],
) -> list[Suggestion]:
    """Handle block suggestions."""
    if not document.is_prose_position(line, 0):
        return []
    source = document.lines[line] if line < len(document.lines) else ""
    fence = FENCE.match(source)
    if fence is not None:
        edit = _language_edit(fence, column)
        block = _opening_at(document, line)
        if edit and block:
            return list(edit.choices(language_names(documents, block, installed)))
    return []
