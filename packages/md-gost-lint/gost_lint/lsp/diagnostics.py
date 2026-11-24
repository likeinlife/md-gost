"""Convert shared lint findings to diagnostics for a snapshot of the open books."""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from lsprotocol import types
from pygls.workspace.position_codec import PositionCodec

from gost_lint.config import ConfigError
from gost_lint.lsp.books import Book, Books
from gost_lint.markdown import Document
from gost_lint.report import Issue

LintReports = dict[Path, list[types.Diagnostic]]
Severity = types.DiagnosticSeverity


@dataclass
class Source:
    """Represent Source."""

    lines: list[str]
    ends: dict[tuple[int, int], int]

    @classmethod
    def from_markdown(cls, document: Document) -> "Source":
        """Build from markdown."""
        ends = {(ref.line, ref.start): ref.end for ref in document.reference_spans()}
        for label, _ in document.definition_spans():
            ends[label.line, label.start] = label.end
        return cls(document.lines, ends)

    def diagnostic(self, issue: Issue, codec: PositionCodec) -> types.Diagnostic:
        """Handle diagnostic."""
        return types.Diagnostic(
            range=codec.range_to_client_units(self.lines, self._range(issue)),
            message=issue.message,
            severity=Severity.Error if issue.level == "error" else Severity.Warning,
            code=issue.rule,
            source="md-lint",
        )

    def _range(self, issue: Issue) -> types.Range:
        last_line = max(len(self.lines) - 1, 0)
        line = min(max(issue.line - 1, 0), last_line)
        width = len(self.lines[line]) if self.lines else 0
        start = min(max(issue.column - 1, 0), width)
        end = self.ends.get((line, start), start + 1)
        return types.Range(
            start=types.Position(line, start),
            end=types.Position(line, min(end, width)),
        )


def _book_reports(book: Book, codec: PositionCodec) -> LintReports:
    sources = {doc.path: Source.from_markdown(doc) for doc in book.work.docs}
    reports: LintReports = defaultdict(list)
    for issue in book.lint():
        path = book.root / issue.path
        if path not in sources:
            lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
            sources[path] = Source(lines, {})
        reports[path].append(sources[path].diagnostic(issue, codec))
    return reports


def _active_reports(books: Books, manifest: Path, codec: PositionCodec) -> LintReports:
    book = books.load(manifest)
    if any(doc.path in books.buffers for doc in book.work.docs):
        return _book_reports(book, codec)
    return {}


def reports_for(books: Books, codec: PositionCodec) -> LintReports:
    """Handle reports for."""
    reports: LintReports = {path: [] for path in books.buffers}
    for manifest in books.active_manifests():
        try:
            reports.update(_active_reports(books, manifest, codec))
        except (OSError, ValueError) as exc:
            origin = types.Position(0, 0)
            source = exc.path if isinstance(exc, ConfigError) else manifest
            reports[source] = [
                types.Diagnostic(
                    range=types.Range(origin, origin),
                    message=str(exc),
                    severity=Severity.Error,
                    source="md-gost-lsp",
                ),
            ]
    return reports
