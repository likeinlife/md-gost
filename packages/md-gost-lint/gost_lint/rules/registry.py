"""Metadata and registration for the Markdown lint rules."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from importlib import import_module
from typing import Any

Check = Callable[..., Iterator[Any]]
RULE_MODULES = (
    "attachments",
    "bold",
    "build",
    "caption",
    "citations",
    "formula_refs",
    "manual_numbers",
    "numbering",
    "refs",
    "reference_order",
    "structure",
    "headings",
    "style",
    "table_numbering",
    "table_caption",
    "table_shape",
    "typo",
    "whitespace",
    "work_refs",
    "work_structure",
)
WORK_SCOPE = "work"
ERROR_LEVEL = "error"
rules: dict[str, "Rule"] = {}


@dataclass
class Rule:
    """Represent Rule."""

    id: str
    level: str
    scope: str
    summary: str
    check: Check


class RuleDecorator:
    """Register a check with the metadata supplied to ``rule``."""

    def __init__(self, rule_id: str, level: str, summary: str, scope: str) -> None:
        """Initialize the instance."""
        self.metadata = (rule_id, level, summary, scope)

    def __call__(self, check: Check) -> Check:
        """Register the check and return it unchanged."""
        rule_id, level, summary, scope = self.metadata
        rules[rule_id] = Rule(rule_id, level, scope, summary, check)
        return check


def rule(rule_id: str, level: str, summary: str, scope: str = "file") -> RuleDecorator:
    """Handle rule."""
    return RuleDecorator(rule_id, level, summary, scope)


def load_all() -> dict[str, Rule]:
    """Load all."""
    for module_name in RULE_MODULES:
        import_module(f".{module_name}", __package__)
    return rules
