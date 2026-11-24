"""Compose bibliography edits against the open versions of a work's chapters."""

from dataclasses import dataclass, field

from lsprotocol import types
from pygls.workspace.position_codec import PositionCodec

from gost_lint.lsp.bibliography import Citation, bibliography_document
from gost_lint.lsp.bibliography_placement import document_newline, entry_position
from gost_lint.lsp.navigation import key_range
from gost_lint.lsp.session import Cursor, GostServer
from gost_lint.lsp.workspace_edits import workspace_edit
from gost_lint.markdown import Document
from gost_lint.markdown.refs import LabelSpan


@dataclass
class BibliographyEdit:
    """Represent Bibliography Edit."""

    target: Document
    selection: types.Range
    edits: dict[str, list[types.TextEdit]] = field(default_factory=dict)

    def add(self, document: Document, edit: types.TextEdit) -> None:
        """Handle add."""
        self.edits.setdefault(document.path.as_uri(), []).append(edit)

    def workspace_edit(self, ls: GostServer) -> types.WorkspaceEdit:
        """Handle workspace edit."""
        return workspace_edit(ls, self.edits)


def _append(document: Document, key: str, codec: PositionCodec) -> BibliographyEdit:
    placement = entry_position(document, codec)
    edit = BibliographyEdit(document, placement.selection(key, codec))
    edit.add(document, placement.entry(key, document_newline(document)))
    return edit


def bibliography_edit(
    cursor: Cursor,
    citation: Citation,
    existing: tuple[Document, LabelSpan] | None,
    codec: PositionCodec,
) -> BibliographyEdit:
    """Handle bibliography edit."""
    if existing:
        document, span = existing
        edit = BibliographyEdit(document, key_range(document, span, codec))
    else:
        edit = _append(bibliography_document(cursor), citation.key, codec)
    if citation.bare:
        span_range = key_range(cursor.document, citation.bare, codec)
        edit.add(cursor.document, types.TextEdit(span_range, f"[@{citation.key}]"))
    return edit
