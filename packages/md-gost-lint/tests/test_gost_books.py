"""Exercise the boundaries of each work, its buffers and its saved configuration."""

import json
import os
from pathlib import Path

import pytest
from lsprotocol.types import DiagnosticSeverity
from pygls.workspace.position_codec import PositionCodec

from gost_lint.lsp.books import Books, Buffer
from gost_lint.lsp.diagnostics import reports_for
from gost_lint.markdown import Document

CHAPTER = "chapter.md"
SOURCE = "sources.md"
MANIFEST = "book.toml"
CONFIG = "mdlint.toml"
REF_RULE = "REF003"
REFERENCE = "# Глава\n\nСсылка [@eq:чужая].\n"
DEFINITION = "<!-- #eq:чужая -->\n\n$$x=1$$\n"
UTF8 = "utf-8"


def _manifest(folder: Path, *chapters: str) -> None:
    folder.mkdir(exist_ok=True)
    (folder / MANIFEST).write_text(f"chapters = {json.dumps(chapters)}", encoding=UTF8)


def _snapshot(root: Path, sources: dict[Path, str]) -> Books:
    buffers: dict[Path, Buffer] = {}
    for path, source in sources.items():
        document = Document.from_text(path, root, source)
        buffers[path] = Buffer(path.as_uri(), 1, document)
    return Books(buffers, (root,))


def _missing(books: Books, path: Path) -> list[DiagnosticSeverity | None]:
    diagnostics = reports_for(books, PositionCodec())[path]
    return [issue.severity for issue in diagnostics if issue.code == REF_RULE]


def test_manifest_scopes_ignore_other_sources(tmp_path: Path) -> None:
    left = tmp_path / "one"
    right = tmp_path / "two"
    _manifest(left, CHAPTER)
    _manifest(right, CHAPTER)
    ignored = left / "tz.md"
    books = _snapshot(
        tmp_path,
        {left / CHAPTER: REFERENCE, ignored: DEFINITION, right / CHAPTER: DEFINITION},
    )
    assert books.for_document(books.buffers[ignored].document) is None
    assert not reports_for(books, PositionCodec())[ignored]
    assert _missing(books, left / CHAPTER) == [DiagnosticSeverity.Error]


def test_cascade_refreshes_after_config_saves(tmp_path: Path) -> None:
    work = tmp_path / "practice"
    _manifest(work, CHAPTER)
    prose = work / CHAPTER
    (tmp_path / CONFIG).write_text('[rules]\nREF003="warning"', encoding=UTF8)
    books = _snapshot(tmp_path, {prose: REFERENCE})
    assert _missing(books, prose) == [DiagnosticSeverity.Warning]
    (work / CONFIG).write_text('[paths."*.md"]\nREF003="off"', encoding=UTF8)
    assert not _missing(books, prose)
    (work / CONFIG).unlink()
    assert _missing(books, prose) == [DiagnosticSeverity.Warning]


class TestDiskChanges:
    def test_unopened_chapter_tracks_disk_changes(self, tmp_path: Path) -> None:
        _manifest(tmp_path, CHAPTER, SOURCE)
        prose = tmp_path / CHAPTER
        source = tmp_path / SOURCE
        books = _snapshot(tmp_path, {prose: REFERENCE})
        source.write_text(DEFINITION, encoding=UTF8)
        assert not _missing(books, prose)
        source.write_text("# Другая глава\n", encoding=UTF8)
        assert _missing(books, prose)
        source.write_text(DEFINITION, encoding=UTF8)
        assert not _missing(books, prose)
        source.unlink()
        assert _missing(books, prose)

    def test_atomic_save_preserving_timestamp(self, tmp_path: Path) -> None:
        _manifest(tmp_path, CHAPTER, SOURCE)
        books = _snapshot(tmp_path, {tmp_path / CHAPTER: REFERENCE})
        source = tmp_path / SOURCE
        source.write_text(DEFINITION, encoding=UTF8)
        assert not _missing(books, tmp_path / CHAPTER)
        previous = source.stat()
        replacement = tmp_path / "replacement.md"
        replacement.write_text(DEFINITION.replace("чужая", "новая"), encoding=UTF8)
        os.utime(replacement, ns=(previous.st_atime_ns, previous.st_mtime_ns))
        replacement.replace(source)
        assert _missing(books, tmp_path / CHAPTER)


class TestInvalidSettings:
    @pytest.mark.parametrize("bad", ["chapters=1", 'chapters="chapter.md"', "chapters=[5]"])
    def test_bad_manifest_is_isolated(self, tmp_path: Path, bad: str) -> None:
        valid = tmp_path / "valid"
        invalid = tmp_path / "invalid"
        _manifest(valid, CHAPTER)
        _manifest(invalid, CHAPTER)
        (invalid / MANIFEST).write_text(bad, encoding=UTF8)
        books = _snapshot(tmp_path, {valid / CHAPTER: REFERENCE, invalid / CHAPTER: REFERENCE})
        issues = reports_for(books, PositionCodec())[invalid / MANIFEST]
        assert issues[0].source == "md-gost-lsp"
        assert "chapters" in issues[0].message
        assert _missing(books, valid / CHAPTER)

    @pytest.mark.parametrize(
        "bad",
        ["[wrong", "paths=2", "rules=1", "skip='*'", "[rules]\nREF003=0"],
    )
    def test_invalid_config_has_own_uri(self, tmp_path: Path, bad: str) -> None:
        _manifest(tmp_path, CHAPTER)
        prose = tmp_path / CHAPTER
        config = tmp_path / CONFIG
        books = _snapshot(tmp_path, {prose: REFERENCE})
        config.write_text(bad, encoding=UTF8)
        reports = reports_for(books, PositionCodec())
        assert reports[config][0].severity == DiagnosticSeverity.Error
        assert tmp_path / MANIFEST not in reports
