"""Register workspace notifications and keep diagnostics synchronized."""

import asyncio

from lsprotocol import types

from gost_lint.lsp.fence_languages import pandoc_languages
from gost_lint.lsp.session import GostServer


def did_open(ls: GostServer, event: types.DidOpenTextDocumentParams) -> None:
    """Handle did open."""
    ls.synchronize(event.text_document.uri, opening=True)


def did_change(ls: GostServer, event: types.DidChangeTextDocumentParams) -> None:
    """Handle did change."""
    ls.synchronize(event.text_document.uri)


def did_save(ls: GostServer, _event: types.DidSaveTextDocumentParams) -> None:
    """Handle did save."""
    ls.refresh()


def did_close(ls: GostServer, event: types.DidCloseTextDocumentParams) -> None:
    """Handle did close."""
    ls.close(event.text_document.uri)


async def initialized(ls: GostServer, _event: types.InitializedParams) -> None:
    """Handle initialized."""
    capabilities = ls.client_capabilities.workspace
    watched = capabilities.did_change_watched_files if capabilities else None
    if watched and watched.dynamic_registration:
        watchers = [types.FileSystemWatcher("**/*.{md,toml,puml,iuml}")]
        options = types.DidChangeWatchedFilesRegistrationOptions(watchers)
        registration = types.Registration(
            "md-gost-files",
            types.WORKSPACE_DID_CHANGE_WATCHED_FILES,
            options,
        )
        await ls.client_register_capability_async(types.RegistrationParams([registration]))
    ls.pandoc_languages = await asyncio.to_thread(pandoc_languages)


def watched_files(ls: GostServer, _event: types.DidChangeWatchedFilesParams) -> None:
    """Handle watched files."""
    ls.refresh()


def register_events(ls: GostServer) -> None:
    """Handle register events."""
    ls.feature(types.TEXT_DOCUMENT_DID_OPEN)(did_open)
    ls.feature(types.TEXT_DOCUMENT_DID_CHANGE)(did_change)
    ls.feature(types.TEXT_DOCUMENT_DID_SAVE)(did_save)
    ls.feature(types.TEXT_DOCUMENT_DID_CLOSE)(did_close)
    ls.feature(types.INITIALIZED)(initialized)
    ls.feature(types.WORKSPACE_DID_CHANGE_WATCHED_FILES)(watched_files)
