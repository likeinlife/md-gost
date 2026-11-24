"""Check the information shown by an editor hovering over a cross-chapter link."""

from pathlib import Path

import pytest
from lsp_client import Client, Message, start_client

from gost_lint.lsp.navigation import hover_title
from gost_lint.markdown import Document

PROSE = "😀 [@bib:a; @bib:b].\nВ таблице [@tbl:plan].\n`[@tbl:plan]`\n[@tbl:unknown]\n"
CAPTIONS = (
    "<!-- #bib:a Первый источник -->\n\n"
    "<!-- #bib:b Второй источник -->\n\n"
    "<!-- #tbl:plan План работ -->\n\n| Этап |\n| --- |\n| Анализ |\n"
)
CAPTION = "План работ"
LIVE_CAPTION = "План на семестр"
EXPRESSION = r"P = Q \cdot C"
FIRST_KEY = (0, 5, 10)
SECOND_KEY = (0, 13, 18)
TABLE_KEY = (1, 12, 20)
URI = "uri"
DOC = "textDocument"
UTF8 = "utf-8"


def _open(client: Client, path: Path, text: str) -> None:
    descriptor = {URI: path.as_uri(), "languageId": "markdown", "version": 1, "text": text}
    client.notify("textDocument/didOpen", {DOC: descriptor})


def _hover(client: Client, path: Path, line: int, column: int) -> Message | None:
    point = {"line": line, "character": column}
    return client.request("textDocument/hover", {DOC: {URI: path.as_uri()}, "position": point})


def _assert_title(client: Client, prose: Path, span: tuple[int, int, int], title: str) -> None:
    line, start, end = span
    assert _hover(client, prose, line, end - 1) == {
        "contents": {"kind": "plaintext", "value": title},
        "range": {
            "start": {"line": line, "character": start},
            "end": {"line": line, "character": end},
        },
    }


def _saved_captions(client: Client, prose: Path) -> None:
    # Two UTF-16 units for the emoji, then two separate keys inside the brackets.
    _assert_title(client, prose, FIRST_KEY, "Первый источник")
    _assert_title(client, prose, SECOND_KEY, "Второй источник")
    _assert_title(client, prose, TABLE_KEY, CAPTION)
    assert _hover(client, prose, 2, 8) is None
    assert _hover(client, prose, 3, 8) is None


def _changed_caption(client: Client, prose: Path, captions: Path) -> None:
    _open(client, captions, CAPTIONS)
    client.notify(
        "textDocument/didChange",
        {
            DOC: {URI: captions.as_uri(), "version": 2},
            "contentChanges": [{"text": CAPTIONS.replace(CAPTION, LIVE_CAPTION)}],
        },
    )
    _assert_title(client, prose, TABLE_KEY, LIVE_CAPTION)
    client.notify("textDocument/didClose", {DOC: {URI: captions.as_uri()}})
    _assert_title(client, prose, TABLE_KEY, CAPTION)


def test_hover_on_cross_chapter_links(tmp_path: Path) -> None:
    folder = tmp_path.resolve()
    (folder / "book.toml").write_text('chapters = ["chapter.md", "sources.md"]', encoding=UTF8)
    prose = folder / "chapter.md"
    captions = folder / "sources.md"
    prose.write_text(PROSE, encoding=UTF8)
    captions.write_text(CAPTIONS, encoding=UTF8)
    with start_client(folder) as client:
        initialized = client.request("initialize", {"rootUri": folder.as_uri(), "capabilities": {}})
        assert initialized["capabilities"]["hoverProvider"]
        client.notify("initialized", {})
        _open(client, prose, PROSE)
        _saved_captions(client, prose)
        _changed_caption(client, prose, captions)
        assert client.request("shutdown") is None
        client.notify("exit", {})


@pytest.mark.parametrize(
    ("key", "markup", "title"),
    [
        ("fig:scheme", "![Устройство](рисунки/a.png){#fig:scheme}", "Устройство"),
        ("lst:body", '```{.python #lst:body caption="Обработчик"}\npass\n```', "Обработчик"),
        ("lst:api", '```{.python #lst:api file="src/app.py"}\n```', "app.py"),
        ("eq:price", f"<!-- #eq:price -->\n\n$$\n{EXPRESSION}\n$$", EXPRESSION),
    ],
)
def test_object_title(key: str, markup: str, title: str, tmp_path: Path) -> None:
    chapter = Document.from_text(tmp_path / "chapter.md", tmp_path, markup)
    assert hover_title([chapter], key) == title
