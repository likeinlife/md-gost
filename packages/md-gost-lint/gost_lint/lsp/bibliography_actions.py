"""Create bibliography entries through the editor's workspace edit and navigation APIs."""

import asyncio
from functools import partial

from lsprotocol import types

from gost_lint.lsp.bibliography import Citation, citation_at, declaration
from gost_lint.lsp.bibliography_edits import BibliographyEdit, bibliography_edit
from gost_lint.lsp.session import Cursor, GostServer

COMMAND = "md-gost.addBibliographyEntry"
QUICK_FIX = types.CodeActionKind.QuickFix


def bibliography_actions(
    ls: GostServer,
    request: types.CodeActionParams,
    cursor: Cursor,
) -> list[types.CodeAction]:
    """Handle bibliography actions."""
    only = request.context.only
    if only and QUICK_FIX not in only:
        return []
    citation = citation_at(cursor)
    if citation is None:
        return []
    return _offer(ls, cursor, citation, request)


def _offer(
    ls: GostServer,
    cursor: Cursor,
    citation: Citation,
    request: types.CodeActionParams,
) -> list[types.CodeAction]:
    existing = declaration(cursor.book.work.docs, citation.key)
    if existing and citation.bare is None:
        return []
    title = (
        f"Оформить ссылку на {citation.key}" if existing else f"Добавить источник {citation.key}"
    )
    action = types.CodeAction(title=title, kind=QUICK_FIX, is_preferred=True)
    workspace = ls.client_capabilities.workspace
    if workspace and workspace.apply_edit:
        action.command = types.Command(
            title,
            COMMAND,
            arguments=[request.text_document.uri, request.range.start, citation.key],
        )
    else:
        edit = bibliography_edit(cursor, citation, existing, ls.workspace.position_codec)
        action.edit = edit.workspace_edit(ls)
    return [action]


def _execute(ls: GostServer, uri: str, point: types.Position, key: str) -> None:
    # Acknowledge the command before editing so Zed keeps focus on the shown source.
    asyncio.get_running_loop().call_soon(_edit_citation, ls, uri, point, key)


def _edit_citation(ls: GostServer, uri: str, point: types.Position, key: str) -> None:
    cursor = ls.cursor(uri, point)
    if cursor is None:
        return
    citation = citation_at(cursor)
    if citation is None or citation.key != key:
        return
    existing = declaration(cursor.book.work.docs, key)
    edit = bibliography_edit(cursor, citation, existing, ls.workspace.position_codec)
    if edit.edits:
        request = types.ApplyWorkspaceEditParams(edit.workspace_edit(ls))
        ls.workspace_apply_edit(request, partial(_reveal, ls, edit))
    else:
        _reveal(ls, edit)


def _reveal(
    ls: GostServer,
    edit: BibliographyEdit,
    response: types.ApplyWorkspaceEditResult | None = None,
) -> None:
    if response and not response.applied:
        return
    window = ls.client_capabilities.window
    if window and window.show_document and window.show_document.support:
        target = types.ShowDocumentParams(
            edit.target.path.as_uri(),
            take_focus=True,
            selection=edit.selection,
        )
        ls.window_show_document(target)


def register_bibliography_command(server: GostServer) -> None:
    """Handle register bibliography command."""
    server.command(COMMAND)(_execute)
