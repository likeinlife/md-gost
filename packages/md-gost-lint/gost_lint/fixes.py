"""Mechanical md-lint repairs shared by the CLI and language server."""

import re
from collections.abc import Collection
from pathlib import Path

from gost_lint.config import Chain
from gost_lint.markdown import Document
from gost_lint.markdown.format_scope import FormatScope
from gost_lint.repairs import Repair, applicable_repairs
from gost_lint.rules.numbering import heading_repairs
from gost_lint.rules.registry import load_all as load_rules
from gost_lint.spacing import WHITESPACE_RULES, spaces
from gost_lint.typography import HYPHEN, QUOTES, typography_repairs
from gost_lint.work import Work

NUMBER_DOT = "STRUCT008"
STRUCTURAL_NUMBER = "STRUCT009"
FIXABLE = (NUMBER_DOT, STRUCTURAL_NUMBER, HYPHEN, QUOTES, *WHITESPACE_RULES)
NEWLINE = re.compile(r"(\r\n|\r|\n)")


def repairs(
    document: Document,
    rules: Collection[str] = FIXABLE,
    scope: FormatScope | None = None,
) -> list[Repair]:
    """Handle repairs."""
    if not rules:
        return []
    scope = scope or document.format_scope
    changes = [entry for entry in spaces(document, scope) if entry.rule in rules]
    changes.extend(
        entry
        for entry in heading_repairs(document)
        if entry.rule in rules and scope.editable(entry.line, entry.start, entry.end)
    )
    changes.extend(typography_repairs(document, rules))
    return changes


def enabled_rules(config: Chain, path: Path, selected: Collection[str] = FIXABLE) -> set[str]:
    """Handle enabled rules."""
    if config.is_skipped(path):
        return set()
    known = load_rules()
    wanted = set(FIXABLE).intersection(selected)
    return {key for key in wanted if config.level_for(known[key], path) != "off"}


def autofix(text: str, rules: Collection[str] = FIXABLE) -> str:
    """Apply safe source edits, retaining original CR, LF or CRLF separators."""
    document = Document.from_text(Path("chapter.md"), Path(), text)
    parts = NEWLINE.split(text)
    for edit in reversed(applicable_repairs(repairs(document, rules))):
        index = 2 * edit.line
        parts[index] = edit.replace(parts[index])
    return "".join(parts)


def _fix_file(path: Path, rules: Collection[str]) -> bool:
    if not rules:
        return False
    with path.open(encoding="utf-8", newline="") as stream:
        original = stream.read()
    fixed = autofix(original, rules)
    if fixed == original:
        return False
    path.write_bytes(fixed.encode("utf-8"))
    return True


def _selected_fix(doc: Document, config: Chain, selected: Collection[str]) -> bool:
    return _fix_file(doc.path, enabled_rules(config, doc.path, selected))


def apply_fixes(works: list[Work], config: Chain, selected: Collection[str]) -> list[str]:
    """Apply fixes."""
    return [
        doc.rel
        for work in works
        for doc in work.docs
        if doc.rel in work.focus and _selected_fix(doc, config, selected)
    ]
