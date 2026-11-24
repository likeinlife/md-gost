"""Round-trip two editor buffers through the real GOST language server."""

from dataclasses import dataclass
from pathlib import Path

from lsp_client import Client, Message, start_client

OPEN = "textDocument/didOpen"
CHANGE = "textDocument/didChange"
CLOSE = "textDocument/didClose"
TEXT_DOC = "textDocument"
MISSING = "REF003"
LIVE = "tbl:live"
UTF8 = "utf-8"
URI = "uri"
RANGE = "range"
# LSP columns count the leading emoji as two UTF-16 units.
PROSE_KEY = (5, 13)
TABLE_KEY = (6, 14)
PROSE_CURSOR = 11


def position(character: int) -> Message:
    return {"line": 0, "character": character}


def key_range(start: int, end: int) -> Message:
    return {"start": position(start), "end": position(end)}


@dataclass
class Book:
    prose: Path
    table: Path

    @classmethod
    def write(cls, folder: Path) -> "Book":
        (folder / "book.toml").write_text('chapters = ["prose.md", "table.md"]', encoding=UTF8)
        prose = folder / "prose.md"
        prose.write_text("😀 [@tbl:disk].\n", encoding=UTF8)
        table = folder / "table.md"
        table.write_text("<!-- #tbl:disk Данные -->\n\n| A | B |\n| --- | --- |\n", encoding=UTF8)
        return cls(prose, table)

    def open(self, client: Client) -> None:
        for path in (self.prose, self.table):
            descriptor = {
                URI: path.as_uri(),
                "languageId": "markdown",
                "version": 1,
                "text": path.read_text(encoding=UTF8),
            }
            client.notify(OPEN, {TEXT_DOC: descriptor})

    def change(self, client: Client, path: Path, edit: Message) -> None:
        client.notify(
            CHANGE,
            {TEXT_DOC: {URI: path.as_uri(), "version": 2}, "contentChanges": [edit]},
        )

    def errors(self, client: Client) -> list[Message]:
        return [
            issue for issue in client.diagnostics(self.prose.as_uri()) if issue["code"] == MISSING
        ]


def _navigation(client: Client, book: Book) -> None:
    prose = {TEXT_DOC: {URI: book.prose.as_uri()}, "position": position(PROSE_CURSOR)}
    candidates = client.request("textDocument/completion", prose)
    choice = next(candidate for candidate in candidates if candidate["label"] == LIVE)
    assert choice["textEdit"] == {RANGE: key_range(*PROSE_KEY), "newText": LIVE}
    target = client.request("textDocument/definition", prose)
    expected = {URI: book.table.as_uri(), RANGE: key_range(*TABLE_KEY)}
    assert target == [expected]


def _references(client: Client, book: Book) -> None:
    declaration = {TEXT_DOC: {URI: book.table.as_uri()}, "position": position(8)}
    declaration["context"] = {"includeDeclaration": False}
    uses = client.request("textDocument/references", declaration)
    expected = {URI: book.prose.as_uri(), RANGE: key_range(*PROSE_KEY)}
    assert uses == [expected]


def _buffers(client: Client, book: Book) -> None:
    book.open(client)
    assert not book.errors(client)
    edit = {RANGE: key_range(9, PROSE_KEY[1]), "text": "live"}
    book.change(client, book.prose, edit)
    missing = book.errors(client)
    assert [issue[RANGE] for issue in missing] == [key_range(*PROSE_KEY)]
    saved = book.table.read_text(encoding=UTF8)
    book.change(client, book.table, {"text": saved.replace("tbl:disk", LIVE)})
    assert not book.errors(client)
    _navigation(client, book)
    _references(client, book)
    client.notify(CLOSE, {TEXT_DOC: {URI: book.table.as_uri()}})
    assert book.errors(client)
    client.notify(CLOSE, {TEXT_DOC: {URI: book.prose.as_uri()}})
    assert not client.diagnostics(book.prose.as_uri())


def test_live_book_over_stdio(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    book = Book.write(root)
    with start_client(root) as client:
        initialized = client.request("initialize", {"rootUri": root.as_uri(), "capabilities": {}})
        assert initialized["capabilities"]["definitionProvider"]
        client.notify("initialized", {})
        _buffers(client, book)
        assert client.request("shutdown") is None
        client.notify("exit", {})
