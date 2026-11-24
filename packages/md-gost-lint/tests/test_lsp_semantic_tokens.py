"""Check semantic overlays independently of the editor's Markdown grammar."""

from pathlib import Path

import pytest
from lsp_client import Client, Message, start_client

from gost_lint.lsp.highlights import highlights
from gost_lint.markdown import Document

SOURCE = """# Обычный заголовок

# Приложение {#пункт .landscape}

[См.](#пункт), [@bib:a; @bib:б] и `[@fig:literal]`.

<!-- #tbl:grid Таблица -->

![Иллюстрация](a.png){#fig:view width=14cm}

```{.python #lst:loop caption="Пример .plot file="}
# Заголовок {#example}
[@tbl:hidden]
```

~~~plantuml
[@fig:скрытая]
~~~

<!-- [@bib:hidden] -->

$$
[@eq:hidden]
$$
"""
SYMBOL = "enumMember"
TYPE = "type"
PROPERTY = "property"
EXPECTED = (
    ("#пункт", SYMBOL, True),
    (".landscape", TYPE, False),
    ("#пункт", SYMBOL, False),
    ("@bib:a", SYMBOL, False),
    ("@bib:б", SYMBOL, False),
    ("#tbl:grid", SYMBOL, True),
    ("#fig:view", SYMBOL, True),
    ("width", PROPERTY, False),
    (".python", TYPE, False),
    ("#lst:loop", SYMBOL, True),
    ("caption", PROPERTY, False),
    ("plantuml", TYPE, False),
)
FULL = "textDocument/semanticTokens/full"
RANGE = "textDocument/semanticTokens/range"
DOC = "textDocument"
PAYLOAD = "data"
UTF8 = "utf-8"
BOOK = 'chapters = ["chapter.md"]'
DRAFT = "😀 [@bib:я; @bib:б]\n<!-- #bib:я Источник -->"


def test_only_gost_markup_has_semantic_tokens(tmp_path: Path) -> None:
    document = Document.from_text(tmp_path / "source.md", tmp_path, SOURCE)
    actual = []
    for token in sorted(highlights(document)):
        line = document.lines[token.line]
        colored = line[token.start : token.end]
        actual.append((colored, token.kind, token.declared))
    assert tuple(actual) == EXPECTED


def _initialize(client: Client, folder: Path, encoding: str) -> None:
    caps = {"general": {"positionEncodings": [encoding]}}
    setup = client.request("initialize", {"rootUri": folder.as_uri(), "capabilities": caps})
    capabilities = setup["capabilities"]
    assert capabilities["positionEncoding"] == encoding
    provider = capabilities["semanticTokensProvider"]
    assert provider["full"]
    assert provider["range"]
    assert provider["legend"]["tokenTypes"] == [SYMBOL, TYPE, PROPERTY]
    assert provider["legend"]["tokenModifiers"] == ["declaration"]
    client.notify("initialized", {})


def _query(client: Client, path: Path, offsets: tuple[int, int, int]) -> None:
    start, delta, size = offsets
    query = {DOC: {"uri": path.as_uri()}}
    encoded = client.request(FULL, query)[PAYLOAD]
    assert encoded[:5] == [0, start, size, 0, 0]
    assert encoded[5:10] == [0, delta, size, 0, 0]
    assert encoded[10:] == [1, 5, size, 0, 1]
    _check_range(client, query, start + delta, size)


def _check_range(client: Client, query: Message, column: int, size: int) -> None:
    begin = {"line": 0, "character": column}
    end = {"line": 0, "character": column + 1}
    query["range"] = {"start": begin, "end": end}
    encoded = client.request(RANGE, query)[PAYLOAD]
    assert encoded == [0, column, size, 0, 0]


def _open(client: Client, path: Path) -> None:
    descriptor: Message = {
        "uri": path.as_uri(),
        "version": 1,
        "languageId": "markdown",
        "text": DRAFT,
    }
    client.notify("textDocument/didOpen", {DOC: descriptor})


ENCODINGS = (
    (UTF8, (6, 9, 7)),
    ("utf-16", (4, 8, 6)),
)


@pytest.mark.parametrize(("encoding", "offsets"), ENCODINGS)
def test_negotiated_full_and_range(
    tmp_path: Path,
    encoding: str,
    offsets: tuple[int, int, int],
) -> None:
    root = tmp_path.resolve()
    path = root / "chapter.md"
    (root / "book.toml").write_text(BOOK, encoding=UTF8)
    path.write_text("старый текст", encoding=UTF8)
    with start_client(root) as client:
        _initialize(client, root, encoding)
        _open(client, path)
        _query(client, path, offsets)
        assert client.request("shutdown") is None
        client.notify("exit", {})
