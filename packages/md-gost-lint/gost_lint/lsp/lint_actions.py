"""Quick fixes for individual md-lint findings and all safe repairs in one buffer."""

from collections.abc import Sequence
from dataclasses import dataclass

from lsprotocol import types

from gost_lint.config import Chain, ConfigError
from gost_lint.fixes import Repair, applicable_repairs, enabled_rules, repairs
from gost_lint.lsp.session import Cursor, GostServer
from gost_lint.lsp.workspace_edits import repair_edit, workspace_edit
from gost_lint.markdown import Document

FIX_ALL = "source.fixAll.md-gost"
QUICK_FIX = types.CodeActionKind.QuickFix
ALL_TITLE = "md-lint: исправить всё в главе"


def _wanted(only: Sequence[str] | None, kind: str) -> bool:
    if not only or "" in only or kind in only:
        return True
    return any(kind.removeprefix(parent).startswith(".") for parent in only)


def _overlaps(edited: types.Range, requested: types.Range) -> bool:
    if requested.start == requested.end:
        return edited.start <= requested.start <= edited.end
    return edited.start < requested.end and requested.start < edited.end


@dataclass
class LintActions:
    """Represent Lint Actions."""

    server: GostServer
    request: types.CodeActionParams
    document: Document

    def local(self, candidates: list[Repair]) -> list[types.CodeAction]:
        """Handle local."""
        actions: list[types.CodeAction] = []
        for repair in candidates:
            edit = repair_edit(self.document, repair, self.server.workspace.position_codec)
            if _overlaps(edit.range, self.request.range):
                actions.append(self._single(repair, edit))
        return actions

    def all(self, candidates: list[Repair]) -> types.CodeAction:
        """Handle all."""
        codec = self.server.workspace.position_codec
        edits = [
            repair_edit(self.document, repair, codec) for repair in applicable_repairs(candidates)
        ]
        return types.CodeAction(title=ALL_TITLE, kind=FIX_ALL, edit=self._workspace_edit(edits))

    def _single(self, repair: Repair, edit: types.TextEdit) -> types.CodeAction:
        matching = [
            diagnostic
            for diagnostic in self.request.context.diagnostics
            if diagnostic.source == "md-lint"
            and diagnostic.code == repair.rule
            and diagnostic.range.start == edit.range.start
        ]
        return types.CodeAction(
            title=f"md-lint: {repair.rule} — {repair.message}",
            kind=QUICK_FIX,
            edit=self._workspace_edit([edit]),
            diagnostics=matching or None,
            is_preferred=True,
        )

    def _workspace_edit(self, edits: list[types.TextEdit]) -> types.WorkspaceEdit:
        return workspace_edit(self.server, {self.request.text_document.uri: edits})


def _candidates(cursor: Cursor) -> list[Repair]:
    try:
        enabled = enabled_rules(Chain(cursor.book.root), cursor.document.path)
    except (OSError, ConfigError):
        return []
    return repairs(cursor.document, enabled)


def lint_actions(
    server: GostServer,
    request: types.CodeActionParams,
    cursor: Cursor,
) -> list[types.CodeAction]:
    """Handle lint actions."""
    local = _wanted(request.context.only, QUICK_FIX)
    fix_all = _wanted(request.context.only, FIX_ALL)
    if not local and not fix_all:
        return []
    candidates = _candidates(cursor)
    builder = LintActions(server, request, cursor.document)
    actions = builder.local(candidates) if local else []
    if fix_all and candidates:
        actions.append(builder.all(candidates))
    return actions
