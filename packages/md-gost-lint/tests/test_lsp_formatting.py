"""Exercise document and selection formatting on unsaved Markdown buffers."""

from pathlib import Path
from types import MappingProxyType

import pytest
from lsp_client import Client, Message, initialized_client, open_markdown

from gost_lint.fixes import autofix

FORMAT = "textDocument/formatting"
RANGE_FORMAT = "textDocument/rangeFormatting"
DOC = "textDocument"
START = "start"
END = "end"
UTF16 = "utf-16-le"
RANGE = "range"
OPTIONS = MappingProxyType({"tabSize": 4, "insertSpaces": True})
PROSE = "📖 Два  слова , затем `x  y` и $a  b$."
CLEAN = "📖 Два слова, затем `x  y` и $a  b$."
TABLE = "|A|B|\r\n|---|---|\r\n|x|два|"
FIXED = "| A   | B   |\r\n| --- | --- |\r\n| x   | два |"
HARD_BREAK = "Перенос  \r\nстроки"
HEADER = '---\r\ntitle: "a  b"\r\n---'
CODE = "```py\r\nx  =  1  \r\n```"
RAW = "<pre>\r\n\r\nx  y  \r\n</pre>"


@pytest.mark.parametrize(
    "literal",
    [
        "<code>a  b</code>",
        "$$ a  b $$",
        '[файл](<dir (a)/name  b> "title )  x")',
        r'{caption="A\"  B"}',
    ],
)
def test_preserve_spaces_inside_markup(literal: str) -> None:
    assert autofix(f"До  {literal}  после") == f"До {literal} после"


def _point(line: int, column: int) -> Message:
    return {"line": line, "character": column}


def _offset(source: str, point: Message) -> int:
    lines = source.split("\n")
    line = point["line"]
    encoded = lines[line].encode(UTF16)
    prefix = encoded[: 2 * point["character"]].decode(UTF16)
    preceding = sum(map(len, lines[:line])) + line
    return preceding + len(prefix)


def _apply(source: str, edits: list[Message]) -> str:
    following = len(source)
    for edit in reversed(edits):
        start = _offset(source, edit[RANGE][START])
        end = _offset(source, edit[RANGE][END])
        assert start <= end <= following
        source = _replace(source, start, end, edit["newText"])
        following = start
    return source


def _replace(source: str, start: int, end: int, text: str) -> str:
    return source[:start] + text + source[end:]


def _format(client: Client, path: Path, request: Message | None = None) -> list[Message]:
    descriptor = {"uri": path.as_uri()}
    arguments = {DOC: descriptor, "options": dict(OPTIONS), **(request or {})}
    method = RANGE_FORMAT if RANGE in arguments else FORMAT
    return client.request(method, arguments)


class TestEditorFormat:
    def test_real_buffer_and_idempotence(self, tmp_path: Path) -> None:
        path = tmp_path / "README.md"
        parts = (HEADER, PROSE, HARD_BREAK, TABLE, CODE, RAW)
        body = "\r\n\r\n".join(parts)
        with initialized_client(tmp_path, {}) as client:
            open_markdown(client, path, body)
            actual = _apply(body, _format(client, path))
            assert actual == body.replace(PROSE, CLEAN).replace(TABLE, FIXED)
            client.notify(
                "textDocument/didChange",
                {DOC: {"uri": path.as_uri(), "version": 2}, "contentChanges": [{"text": actual}]},
            )
            assert not _format(client, path)
        assert not path.exists()

    def test_selection_expands_only_the_touched_table(self, tmp_path: Path) -> None:
        path = tmp_path / "chapter.md"
        body = f"{PROSE}\r\n\r\n{TABLE}\r\n\r\n{PROSE}"
        with initialized_client(tmp_path, {}) as client:
            open_markdown(client, path, body)
            span = {START: _point(3, 1), END: _point(4, 0)}
            edits = _format(client, path, {RANGE: span})
            assert _apply(body, edits) == body.replace(TABLE, FIXED)
            span = {START: _point(0, 0), END: _point(2, 0)}
            edits = _format(client, path, {RANGE: span})
            assert _apply(body, edits) == body.replace(PROSE, CLEAN, 1)

    def test_eof_and_trailing_preferences(self, tmp_path: Path) -> None:
        path = tmp_path / "intro.md"
        body = f"{HARD_BREAK} \r\n\r\n"
        options = {**OPTIONS, "trimTrailingWhitespace": False, "trimFinalNewlines": True}
        with initialized_client(tmp_path, {}) as client:
            open_markdown(client, path, body)
            edits = _format(client, path, {"options": options})
            assert _apply(body, edits) == f"{HARD_BREAK}\r\n"
