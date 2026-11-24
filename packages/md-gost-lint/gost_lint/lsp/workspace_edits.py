"""Package text edits with the editor's current document versions when available."""

from lsprotocol import types
from pygls.workspace.position_codec import PositionCodec

from gost_lint.fixes import Repair
from gost_lint.lsp.session import GostServer
from gost_lint.markdown import Document


def workspace_edit(
    server: GostServer,
    edits: dict[str, list[types.TextEdit]],
) -> types.WorkspaceEdit:
    """Handle workspace edit."""
    workspace = server.client_capabilities.workspace
    support = workspace.workspace_edit if workspace else None
    if support and support.document_changes:
        return _versioned(server, edits)
    return types.WorkspaceEdit(changes=edits)


def _versioned(server: GostServer, edits: dict[str, list[types.TextEdit]]) -> types.WorkspaceEdit:
    versions = {buffer.uri: buffer.version for buffer in server.opened.values()}
    changes = [
        types.TextDocumentEdit(
            types.OptionalVersionedTextDocumentIdentifier(uri, versions.get(uri)),
            replacements,
        )
        for uri, replacements in edits.items()
    ]
    return types.WorkspaceEdit(document_changes=changes)


def repair_edit(document: Document, repair: Repair, codec: PositionCodec) -> types.TextEdit:
    """Handle repair edit."""
    start = types.Position(repair.line, repair.start)
    end = types.Position(repair.line, repair.end)
    bounds = codec.range_to_client_units(document.lines, types.Range(start, end))
    return types.TextEdit(bounds, repair.text)
