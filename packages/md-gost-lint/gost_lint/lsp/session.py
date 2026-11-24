"""State of one LSP client and the versions used for live diagnostics."""

import asyncio
from dataclasses import dataclass
from pathlib import Path

from lsprotocol import types
from pygls import uris
from pygls.lsp.server import LanguageServer
from pygls.workspace import Workspace
from pygls.workspace.position_codec import PositionCodec

from gost_lint.lsp.books import Book, Books, Buffer, config_root, find_manifest
from gost_lint.lsp.completion_files import warm_file_catalog
from gost_lint.lsp.diagnostics import LintReports, reports_for
from gost_lint.markdown import Document

DEBOUNCE_SECONDS = 0.15


@dataclass
class Cursor:
    """Represent Cursor."""

    document: Document
    book: Book
    position: types.Position


def workspace_folders(workspace: Workspace) -> tuple[Path, ...]:
    """Handle workspace folders."""
    paths = (uris.to_fs_path(entry.uri) for entry in workspace.folders.values())
    folders = [Path(path).resolve() for path in paths if path]
    if workspace.root_path:
        folders.append(Path(workspace.root_path).resolve())
    return tuple(folders)


def cursor_for(
    document: Document,
    book: Book,
    position: types.Position,
    codec: PositionCodec,
) -> Cursor:
    """Handle cursor for."""
    lines = [*document.lines, ""]
    point = codec.position_from_client_units(lines, position)
    return Cursor(document, book, types.Position(point.line, point.character))


class GostServer(LanguageServer):
    """Represent Gost Server."""

    def __init__(self) -> None:
        """Initialize the instance."""
        super().__init__("md-gost-lsp", "0.1.0")
        self.pandoc_languages: frozenset[str] = frozenset()
        self.opened: dict[Path, Buffer] = {}
        self.published: dict[Path, str] = {}
        self.pending: asyncio.Task[None] | None = None

    def synchronize(self, uri: str, *, opening: bool = False) -> None:
        """Handle synchronize."""
        if not uri.startswith("file:"):
            return
        buffer = self.workspace.get_text_document(uri)
        path = Path(buffer.path).resolve()
        if path.suffix.lower() == ".md":
            manifest = find_manifest(path)
            root = config_root(manifest or path, workspace_folders(self.workspace))
            document = Document.from_text(path, root, buffer.source)
            self.opened[path] = Buffer(uri, buffer.version, document)
            if opening and manifest:
                asyncio.get_running_loop().run_in_executor(None, warm_file_catalog, manifest.parent)
        self.refresh()

    def close(self, uri: str) -> None:
        """Handle close."""
        path = uris.to_fs_path(uri)
        if path:
            self.opened.pop(Path(path).resolve(), None)
        self.refresh()

    def cursor(self, uri: str, position: types.Position) -> Cursor | None:
        """Handle cursor."""
        context = document_book(self, uri)
        if context is None:
            return None
        document, book = context
        return cursor_for(document, book, position, self.workspace.position_codec)

    def refresh(self) -> None:
        """Handle refresh."""
        if self.pending is not None:
            self.pending.cancel()
        self.pending = asyncio.create_task(self._diagnose())

    async def _diagnose(self) -> None:
        await asyncio.sleep(DEBOUNCE_SECONDS)
        snapshot = Books(self.opened.copy(), workspace_folders(self.workspace))
        reports = await asyncio.to_thread(reports_for, snapshot, self.workspace.position_codec)
        self._publish(reports)

    def _publish(self, reports: LintReports) -> None:
        published: dict[Path, str] = {}
        for path, diagnostics in reports.items():
            opened = self.opened.get(path)
            uri = opened.uri if opened else path.as_uri()
            self.text_document_publish_diagnostics(
                types.PublishDiagnosticsParams(
                    uri,
                    diagnostics,
                    opened.version if opened else None,
                ),
            )
            published[path] = uri
        for path in self.published.keys() - published.keys():
            self.text_document_publish_diagnostics(
                types.PublishDiagnosticsParams(self.published[path], []),
            )
        self.published = published


def open_buffer(server: GostServer, uri: str) -> Buffer | None:
    """Open buffer."""
    path = uris.to_fs_path(uri)
    return server.opened.get(Path(path).resolve()) if path else None


def document_book(server: GostServer, uri: str) -> tuple[Document, Book] | None:
    """Handle document book."""
    opened = open_buffer(server, uri)
    if opened is None:
        return None
    books = Books(server.opened, workspace_folders(server.workspace))
    try:
        book = books.for_document(opened.document)
    except (OSError, ValueError):
        return None
    if book is None:
        return None
    return opened.document, book
