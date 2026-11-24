"""Exercise quick fixes against unsaved text, the configuration cascade and UTF-16."""

from pathlib import Path

import pytest
from lsp_client import Message, initialized_client, open_markdown

FIX_ALL = "source.fixAll.md-gost"
QUICK_FIX = "quickfix"
SOURCE = "# 2. Заключение\r\n\r\n😀 До  слова , потом\tтекст. \r\n"
CHAPTER = "chapter.md"
OTHER = "other.md"
DOT = "STRUCT008"
SPACE = "TYPO003"
EDIT = "edit"
CONTEXT = "context"
CHANGES = "changes"
RANGE = "range"
START = "start"
END = "end"
KIND = "kind"
METHOD = "textDocument/codeAction"
VERSION = 23


@pytest.fixture
def chapter(tmp_path: Path) -> Path:
    work = tmp_path / "book"
    work.mkdir()
    (work / "book.toml").write_text(f'chapters=["{CHAPTER}","{OTHER}"]')
    (work / OTHER).write_text("# 1. Введение\n")
    path = work / CHAPTER
    path.write_text("# На диске\n")
    return path.resolve()


def _point(line: int, column: int) -> Message:
    return {"line": line, "character": column}


def _arguments(path: Path, point: Message, only: list[str]) -> Message:
    return {
        "textDocument": {"uri": path.as_uri()},
        RANGE: {START: point, END: point},
        CONTEXT: {"only": only, "diagnostics": []},
    }


def _only(entries: list[Message]) -> Message:
    assert len(entries) == 1
    return entries[0]


def _span(line: int, start: int, end: int) -> Message:
    return {START: _point(line, start), END: _point(line, end)}


class TestQuickFix:
    def test_single_matches_exact_occurrence(self, chapter: Path) -> None:
        with initialized_client(chapter.parent, {}) as client:
            open_markdown(client, chapter, SOURCE, VERSION)
            request = _arguments(chapter, _point(2, 6), [QUICK_FIX])
            diagnostic = self._diagnostic()
            request[CONTEXT]["diagnostics"] = [diagnostic]
            action = _only(client.request(METHOD, request))
            assert action[KIND] == QUICK_FIX
            assert SPACE in action["title"]
            assert action["diagnostics"] == [diagnostic]
            edit = _only(action[EDIT][CHANGES][chapter.as_uri()])
            assert edit == {RANGE: _span(2, 5, 7), "newText": " "}

    def test_menu_offers_fix_all_away_from_findings(self, chapter: Path) -> None:
        with initialized_client(chapter.parent, {}) as client:
            open_markdown(client, chapter, SOURCE)
            menu = _arguments(chapter, _point(1, 0), [])
            action = _only(client.request(METHOD, menu))
            assert action[KIND] == FIX_ALL
            for kind in (QUICK_FIX, "refactor"):
                menu[CONTEXT]["only"] = [kind]
                assert not client.request(METHOD, menu)

    def _diagnostic(self) -> Message:
        return {
            "source": "md-lint",
            "code": SPACE,
            "message": "два пробела подряд",
            RANGE: {START: _point(2, 5), END: _point(2, 6)},
        }


class TestFixAll:
    @pytest.mark.parametrize("kind", ["source", "source.fixAll", FIX_ALL])
    def test_versioned_edit_contains_only_this_buffer(self, chapter: Path, kind: str) -> None:
        capabilities = {"workspace": {"workspaceEdit": {"documentChanges": True}}}
        with initialized_client(chapter.parent, capabilities) as client:
            open_markdown(client, chapter, SOURCE, VERSION)
            menu = _arguments(chapter, _point(1, 0), [kind])
            action = _only(client.request(METHOD, menu))
            assert action[KIND] == FIX_ALL
            change = _only(action[EDIT]["documentChanges"])
            assert change["textDocument"] == {"uri": chapter.as_uri(), "version": VERSION}
            self._check_repairs(change["edits"])

    def test_only_enabled_rules(self, chapter: Path) -> None:
        config = chapter.parent / "mdlint.toml"
        config.write_text('[rules]\nSTRUCT009 = "off"\nTYPO003 = "off"\nTYPO005 = "off"')
        with initialized_client(chapter.parent, {}) as client:
            open_markdown(client, chapter, SOURCE)
            request = _arguments(chapter, _point(0, 3), [QUICK_FIX])
            action = _only(client.request(METHOD, request))
            assert DOT in action["title"]
            request[CONTEXT]["only"] = [FIX_ALL]
            action = _only(client.request(METHOD, request))
            edit = _only(action[EDIT][CHANGES][chapter.as_uri()])
            assert edit[RANGE] == _span(0, 3, 4)
            config.write_text('skip = ["chapter.md"]')
            assert not client.request(METHOD, request)

    def _check_repairs(self, edits: list[Message]) -> None:
        expected = [
            (0, 2, 5, ""),
            (2, 5, 7, " "),
            (2, 12, 13, ""),
            (2, 20, 21, " "),
            (2, 27, 28, ""),
        ]
        actual = [
            (
                edit[RANGE][START]["line"],
                edit[RANGE][START]["character"],
                edit[RANGE][END]["character"],
                edit["newText"],
            )
            for edit in edits
        ]
        assert actual == expected
