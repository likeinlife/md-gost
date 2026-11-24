"""Offer lint fixes and bibliography actions through the same LSP menu."""

from lsprotocol import types

from gost_lint.lsp.bibliography_actions import bibliography_actions, register_bibliography_command
from gost_lint.lsp.lint_actions import FIX_ALL, lint_actions
from gost_lint.lsp.session import GostServer


def code_actions(server: GostServer, request: types.CodeActionParams) -> list[types.CodeAction]:
    """Handle code actions."""
    cursor = server.cursor(request.text_document.uri, request.range.start)
    if cursor is None:
        return []
    actions = bibliography_actions(server, request, cursor)
    actions.extend(lint_actions(server, request, cursor))
    return actions


def register_code_actions(server: GostServer) -> None:
    """Handle register code actions."""
    register_bibliography_command(server)
    kinds = types.CodeActionOptions(code_action_kinds=[types.CodeActionKind.QuickFix, FIX_ALL])
    server.feature(types.TEXT_DOCUMENT_CODE_ACTION, kinds)(code_actions)
