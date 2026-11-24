"""Resolve Markdown section links across the chapters a writer sees as one book."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from lsp_client import Client, Message, start_client

UTF8 = "utf-8"
DOC = "textDocument"
URI = "uri"
HOVER = "textDocument/hover"
AUTO_LINE = 11
WRONG_LINE = 12
PROSE = "chapter.md"
APPENDIX = "appendix.md"
KEY = "appendix-acceptance"
TITLE = "Приложение А. Матрица приёмки"
LINK = f"[приложении А](#{KEY})"
LINK_START = 7  # "😀 См. " in UTF-16 code units.
LINK_END = LINK_START + len(LINK)
HEADING = f"# {TITLE} {{#{KEY} .landscape}}"
INTRO = (
    f"# Итоги\n\n😀 См. {LINK}.\n"
    f"См. [матрицу]({APPENDIX}#{KEY}).\n"
    f"\n`{LINK}`\n\n```markdown\n{LINK}\n```\n"
    f"\n[Подробнее](#итоги-1)\n[Ошибка]({PROSE}#{KEY})\n"
)
TARGET = f"{HEADING}\n\n## Итоги\n\nСм. {LINK}.\n"
DEFINITION = "textDocument/definition"
REFERENCES = "textDocument/references"
CURSORS = ((2, "приложении"), (2, KEY), (3, KEY))
RANGE = "range"
START = "start"
END = "end"
CHAR = "character"
LINE = "line"


def _point(line: int, column: int) -> Message:
    return {LINE: line, CHAR: column}


def _at(path: Path, line: int, column: int) -> Message:
    return {DOC: {URI: path.as_uri()}, "position": _point(line, column)}


def _column(path: Path, line: int, word: str) -> int:
    source = path.read_text(encoding=UTF8).splitlines()[line]
    prefix = source[: source.index(word)]
    return len(prefix.encode("utf-16-le")) // 2


def _location(path: Path, line: int) -> Message:
    # UTF-16 columns count the emoji on the first link line as two units.
    start = _column(path, line, KEY)
    end = start + len(KEY)
    bounds = {START: _point(line, start), END: _point(line, end)}
    return {URI: path.as_uri(), RANGE: bounds}


def _open(client: Client, path: Path, text: str) -> None:
    descriptor = {URI: path.as_uri(), "languageId": "markdown", "version": 1, "text": text}
    client.notify("textDocument/didOpen", {DOC: descriptor})


@pytest.fixture
def client(tmp_path: Path) -> Iterator[Client]:
    folder = tmp_path.resolve()
    (folder / "book.toml").write_text(f'chapters = ["{PROSE}", "{APPENDIX}"]', encoding=UTF8)
    (folder / PROSE).write_text(INTRO, encoding=UTF8)
    (folder / APPENDIX).write_text(TARGET, encoding=UTF8)
    (folder / "unused.md").write_text(TARGET, encoding=UTF8)
    with start_client(folder) as connection:
        options = connection.request("initialize", {"rootUri": folder.as_uri(), "capabilities": {}})
        assert "documentLinkProvider" in options["capabilities"]
        assert "#" in options["capabilities"]["completionProvider"]["triggerCharacters"]
        connection.notify("initialized", {})
        _open(connection, folder / PROSE, INTRO)
        yield connection
        assert connection.request("shutdown") is None
        connection.notify("exit", {})


class TestSectionNavigation:
    @pytest.mark.parametrize((LINE, "word"), CURSORS)
    def test_jump_to_unopened_appendix(
        self,
        client: Client,
        tmp_path: Path,
        line: int,
        word: str,
    ) -> None:
        prose = tmp_path.resolve() / PROSE
        column = _column(prose, line, word) + 1
        request = _at(prose, line, column)
        expected = _location(tmp_path.resolve() / APPENDIX, 0)
        assert client.request(DEFINITION, request) == [expected]
        hover = client.request(HOVER, request)
        assert hover["contents"]["value"] == TITLE
        if hover.get(RANGE):
            self._assert_contains(hover[RANGE], column)

    @pytest.mark.parametrize("declarations", [True, False])
    @pytest.mark.parametrize("from_link", [True, False])
    def test_section_references(
        self,
        client: Client,
        tmp_path: Path,
        *,
        declarations: bool,
        from_link: bool,
    ) -> None:
        prose = tmp_path.resolve() / PROSE
        appendix = prose.with_name(APPENDIX)
        _open(client, appendix, TARGET)
        cursor = _at(appendix, 0, HEADING.index(KEY))
        if from_link:
            cursor = _at(prose, 2, _column(prose, 2, KEY))
        cursor["context"] = {"includeDeclaration": declarations}
        expected = [_location(prose, line) for line in (2, 3)]
        expected.append(_location(appendix, 4))
        if declarations:
            expected.append(_location(appendix, 0))
        actual = client.request(REFERENCES, cursor)
        assert len(actual) == len(expected)
        assert all(location in actual for location in expected)

    def test_auto_identifier_uses_manifest_order(self, client: Client, tmp_path: Path) -> None:
        folder = tmp_path.resolve()
        request = _at(folder / PROSE, AUTO_LINE, len("[Подробнее](#итоги"))
        target = client.request(DEFINITION, request)
        assert len(target) == 1
        assert target[0][URI] == (folder / APPENDIX).as_uri()
        heading_line = 2
        assert target[0][RANGE][START][LINE] == heading_line

    def test_wrong_chapter_keeps_fragment_unresolved(self, client: Client, tmp_path: Path) -> None:
        prose = tmp_path.resolve() / PROSE
        request = _at(prose, WRONG_LINE, _column(prose, WRONG_LINE, KEY))
        assert not client.request(DEFINITION, request)
        assert client.request(HOVER, request) is None

    def test_section_hover_tracks_open_buffer(self, client: Client, tmp_path: Path) -> None:
        folder = tmp_path.resolve()
        changed = "Приложение А. Проверки"
        _open(client, folder / APPENDIX, TARGET.replace(TITLE, changed))
        request = _at(folder / PROSE, 2, len("😀 См. [приложении"))
        assert client.request(HOVER, request)["contents"]["value"] == changed
        client.notify("textDocument/didClose", {DOC: {URI: (folder / APPENDIX).as_uri()}})
        assert client.request(HOVER, request)["contents"]["value"] == TITLE

    def test_clickable_section_links(self, client: Client, tmp_path: Path) -> None:
        prose = tmp_path.resolve() / PROSE
        links = client.request("textDocument/documentLink", {DOC: {URI: prose.as_uri()}})
        by_line = {link[RANGE][START][LINE]: link for link in links}
        assert set(by_line) == {2, 3, AUTO_LINE}
        assert by_line[2][RANGE][START] == _point(2, LINK_START)
        assert by_line[2][RANGE][END] == _point(2, LINK_END)
        appendix = prose.with_name(APPENDIX).as_uri()
        column = HEADING.index(KEY) + 1
        assert by_line[2]["target"] == f"{appendix}#1,{column}"

    def _assert_contains(self, bounds: Message, column: int) -> None:
        assert bounds[START][CHAR] <= column < bounds[END][CHAR]
