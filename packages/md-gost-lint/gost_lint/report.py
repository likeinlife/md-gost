"""Issue formatting: a clickable `path:line:col:` line per finding."""

import json
from dataclasses import asdict, dataclass
from types import MappingProxyType

COLORS = MappingProxyType({"error": "\033[31m", "warning": "\033[33m"})
RESET = "\033[0m"


@dataclass
class Issue:
    """Represent Issue."""

    path: str
    line: int
    column: int
    level: str
    rule: str
    message: str

    def sort_key(self) -> tuple[str, int, int, str]:
        """Handle sort key."""
        return (self.path, self.line, self.column, self.rule)


def _issue_line(issue: Issue, tag: str) -> str:
    """Format one finding as a clickable location line."""
    location = f"{issue.path}:{issue.line}:{issue.column}"
    prefix = f"{location}: {tag}"
    detail = f"[{issue.rule}] {issue.message}"
    return f"{prefix} {detail}"


def text_report(issues: list[Issue], *, color: bool = True) -> str:
    """Handle text report."""
    out: list[str] = []
    for issue in sorted(issues, key=Issue.sort_key):
        level_color = COLORS[issue.level] if color else ""
        tag = f"{level_color}{issue.level}{RESET}" if color else issue.level
        out.append(_issue_line(issue, tag))
    return "\n".join(out)


def json_report(issues: list[Issue]) -> str:
    """Handle json report."""
    return json.dumps(
        [asdict(issue) for issue in sorted(issues, key=Issue.sort_key)],
        ensure_ascii=False,
        indent=1,
    )


def summary(issues: list[Issue]) -> str:
    """Handle summary."""
    errors = sum(1 for issue in issues if issue.level == "error")
    warnings = sum(1 for issue in issues if issue.level == "warning")
    if not issues:
        return "md-lint: замечаний нет"
    return f"md-lint: ошибок — {errors}, предупреждений — {warnings}"
