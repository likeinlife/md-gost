"""Exercise citation quick fixes, including the editor's edit and navigation round trip."""

from pathlib import Path

import pytest
from lsp_client import Client, Message, initialized_client, open_markdown

DOC = "textDocument"
BIB = "bib:новый"
BARE = f"#{BIB}"
GROUP = f"[@bib:старый; @{BIB}]"
CITATION = f"[@{BIB}]"
MARKER = "<!-- #bib:старый Книга -->"
DESCRIPTION = "Описание источника"
NEW_MARKER = f"<!-- #{BIB} {DESCRIPTION} -->"
PROSE = "chapter.md"
BIBLIOGRAPHY = "REFERENCES.md"
UTF8 = "utf-8"
CODE_ACTION = "textDocument/codeAction"
SHOW = "window/showDocument"
APPLY = "workspace/applyEdit"
COMMAND = "md-gost.addBibliographyEntry"
COMMAND_FIELD = "command"
URI = "uri"
CHANGES = "changes"
EDIT = "edit"
NEW_TEXT = "newText"
RANGE = "range"
VERSION = 7
START = "start"
END = "end"
GROUP_LINE = f"📖 {GROUP}"
GROUP_COLUMN = len(GROUP_LINE.encode()) - 1
BARE_END = 3 + len(BARE)


def _point(line: int, column: int) -> Message:
    return {"line": line, "character": column}


def _actions(client: Client, path: Path, column: int, line: int = 0) -> list[Message]:
    point = _point(line, column)
    bounds = {START: point, END: point}
    identifier = {URI: path.as_uri()}
    request: Message = {DOC: identifier, RANGE: bounds, "context": {"diagnostics": []}}
    return client.request(CODE_ACTION, request)


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    root = tmp_path.resolve()
    (root / "book.toml").write_text(f'chapters=["{PROSE}", "{BIBLIOGRAPHY}"]', encoding=UTF8)
    (root / PROSE).touch()
    (root / BIBLIOGRAPHY).write_bytes(f"{MARKER}\r\n".encode())
    return root


def _assert_append(edit: Message, line: int) -> None:
    point = _point(line, 0)
    assert edit[RANGE] == {START: point, END: point}
    assert edit[NEW_TEXT] == f"\r\n{NEW_MARKER}\r\n"


class TestEditorCommand:
    def capabilities(self) -> Message:
        return {
            "general": {"positionEncodings": [UTF8]},
            "workspace": {"applyEdit": True, "workspaceEdit": {"documentChanges": True}},
            "window": {"showDocument": {"support": True}},
        }

    def test_grouped_citation_in_open_version(self, folder: Path) -> None:
        chapter = folder / PROSE
        references = folder / BIBLIOGRAPHY
        with initialized_client(folder, self.capabilities()) as client:
            open_markdown(client, chapter, GROUP_LINE)
            action = _actions(client, chapter, GROUP_COLUMN)[0]
            assert action["title"] == f"Добавить источник {BIB}"
            assert action[COMMAND_FIELD][COMMAND_FIELD] == COMMAND
            open_markdown(
                client,
                references,
                f"# Черновик\r\n\r\n{MARKER}\r\n\r\n# Приложение\r\n",
                VERSION,
            )
            assert client.request("workspace/executeCommand", action[COMMAND_FIELD]) is None
            self._check_edit(client, references)

    def _check_edit(self, client: Client, references: Path) -> None:
        applied = client.answer(APPLY, {"applied": True})
        changes = applied[EDIT]["documentChanges"]
        assert len(changes) == 1
        change = changes[0]
        assert change[DOC] == {URI: references.as_uri(), "version": VERSION}
        _assert_append(change["edits"][0], 3)
        shown = client.answer(SHOW, {"success": True})
        assert shown[URI] == references.as_uri()
        assert shown["takeFocus"]
        self._check_selection(shown["selection"], 4)

    def _check_selection(self, selection: Message, line: int) -> None:
        start = len(f"<!-- #{BIB} ".encode())
        end = start + len(DESCRIPTION.encode())
        assert selection == {START: _point(line, start), END: _point(line, end)}


class TestDirectEdit:
    def test_bare_token_and_closed_crlf_file(self, folder: Path) -> None:
        chapter = folder / PROSE
        with initialized_client(folder, {}) as client:
            open_markdown(client, chapter, f"😀 {BARE}")
            action = _actions(client, chapter, BARE_END)[0]
            changes = action[EDIT][CHANGES]
            assert COMMAND_FIELD not in action
            _assert_append(changes[(folder / BIBLIOGRAPHY).as_uri()][0], 1)
            bounds = {START: _point(0, 3), END: _point(0, BARE_END)}
            assert changes[chapter.as_uri()] == [{NEW_TEXT: CITATION, RANGE: bounds}]

    def test_existing_source_normalizes_bare_tokens(self, folder: Path) -> None:
        chapter = folder / PROSE
        with initialized_client(folder, {}) as client:
            open_markdown(client, chapter, "#bib:старый\n\n[@bib:старый]")
            action = _actions(client, chapter, 1)[0]
            changes = action[EDIT][CHANGES]
            assert list(changes) == [chapter.as_uri()]
            assert changes[chapter.as_uri()][0][NEW_TEXT] == "[@bib:старый]"
            assert not _actions(client, chapter, 2, 2)

    @pytest.mark.parametrize("wrapped", ["`{}`", "<!-- {} -->", "~~~py\n{}\n~~~", "[адрес]({})"])
    def test_literal_and_fragment(self, folder: Path, wrapped: str) -> None:
        chapter = folder / PROSE
        source = wrapped.format(BARE)
        prefix = source.partition(BARE)[0].split("\n")
        with initialized_client(folder, {}) as client:
            open_markdown(client, chapter, source)
            column = len(prefix[-1]) + 1
            assert not _actions(client, chapter, column, len(prefix) - 1)

    @pytest.mark.parametrize("first", [True, False])
    def test_single_chapter_before_appendix(self, folder: Path, *, first: bool) -> None:
        chapter = folder / PROSE
        (folder / "book.toml").write_text(f'chapters=["{PROSE}"]', encoding=UTF8)
        body = "# Список использованных источников\n\n## Законы\n\n# Приложение"
        source = "\n\n".join((BARE, body) if first else (body, BARE))
        with initialized_client(folder, {}) as client:
            open_markdown(client, chapter, source)
            self._check_section(client, chapter, first=first)

    def test_bare_key_at_end_of_single_file(self, folder: Path) -> None:
        chapter = folder / PROSE
        (folder / "book.toml").write_text(f'chapters=["{PROSE}"]', encoding=UTF8)
        with initialized_client(folder, {}) as client:
            open_markdown(client, chapter, BARE)
            action = _actions(client, chapter, len(BARE))[0]
            edits = action[EDIT][CHANGES][chapter.as_uri()]
            insertion = edits[0][RANGE][START]
            assert insertion == edits[1][RANGE][END]
            assert edits[0][NEW_TEXT] == f"\n\n{NEW_MARKER}\n"
            assert edits[1][NEW_TEXT] == CITATION

    def _check_section(self, client: Client, chapter: Path, *, first: bool) -> None:
        citation_line = 0 if first else 6
        action = _actions(client, chapter, len(BARE), citation_line)[0]
        edits = action[EDIT][CHANGES][chapter.as_uri()]
        insertion = _point(6 if first else 4, 0)
        assert edits[0][RANGE] == {START: insertion, END: insertion}
        assert edits[0][NEW_TEXT] == f"{NEW_MARKER}\n\n"
        assert edits[1][NEW_TEXT] == CITATION
        assert edits[1][RANGE][START] == _point(citation_line, 0)
