"""Apply registered lint rules to resolved works."""

from dataclasses import dataclass
from pathlib import Path

from gost_lint.config import Chain
from gost_lint.markdown import Document
from gost_lint.paths import relative_path
from gost_lint.report import Issue
from gost_lint.rules.registry import Rule
from gost_lint.work import Work


@dataclass
class RuleRun:
    """Represent Rule Run."""

    works: list[Work]
    rules: dict[str, Rule]
    config: Chain
    root: Path
    selected: set[str]
    ignored: set[str]


@dataclass
class IssuePosition:
    """Represent Issue Position."""

    line: int
    column: int
    message: str


class IssueBuilder:
    """Construct report issues after applying scope and severity settings."""

    def document(
        self,
        document: Document,
        work: Work,
        rule: Rule,
        config: Chain,
        position: IssuePosition,
    ) -> Issue | None:
        """Handle document."""
        if document.rel not in work.focus or config.is_skipped(document.path):
            return None
        level = config.level_for(rule, document.path)
        if level == "off":
            return None
        return Issue(
            document.rel,
            position.line,
            position.column,
            level,
            rule.id,
            position.message,
        )

    def path(
        self,
        target: Path,
        rule: Rule,
        config: Chain,
        root: Path,
        position: IssuePosition,
    ) -> Issue | None:
        """Handle path."""
        level = config.level_for(rule, target)
        if level == "off":
            return None
        return Issue(
            relative_path(target, root),
            position.line,
            position.column,
            level,
            rule.id,
            position.message,
        )


class RuleRunner:
    """Run file and work rules over each requested work."""

    def __init__(self, request: RuleRun) -> None:
        """Initialize the instance."""
        self.request = request
        self.issue_builder = IssueBuilder()

    def run(self) -> list[Issue]:
        """Handle run."""
        issues: list[Issue] = []
        for work in self.request.works:
            for rule in self.request.rules.values():
                if not self._selected(rule):
                    continue
                if rule.scope == "file":
                    issues.extend(self._file_issues(work, rule))
                else:
                    issues.extend(self._work_issues(work, rule))
        return issues

    def _selected(self, rule: Rule) -> bool:
        chosen = self.request.selected
        ignored = self.request.ignored
        return (not chosen or rule.id in chosen) and rule.id not in ignored

    def _file_issues(self, work: Work, rule: Rule) -> list[Issue]:
        issues: list[Issue] = []
        for document in work.docs:
            if document.rel not in work.focus or self.request.config.is_skipped(document.path):
                continue
            issues.extend(self._document_issues(document, work, rule))
        return issues

    def _document_issues(self, document: Document, _work: Work, rule: Rule) -> list[Issue]:
        config = self.request.config
        level = config.level_for(rule, document.path)
        if level == "off":
            return []
        return [
            Issue(document.rel, line, column, level, rule.id, message)
            for line, column, message in rule.check(document)
        ]

    def _work_issues(self, work: Work, rule: Rule) -> list[Issue]:
        issues: list[Issue] = []
        for finding in rule.check(work):
            where = finding[0]
            position = IssuePosition(*finding[1:])
            issue = self._issue_for_location(where, work, rule, position)
            if issue is not None:
                issues.append(issue)
        return issues

    def _issue_for_location(
        self,
        where: Path | Document | None,
        work: Work,
        rule: Rule,
        position: IssuePosition,
    ) -> Issue | None:
        if isinstance(where, Document):
            return self.issue_builder.document(where, work, rule, self.request.config, position)
        target = where or work.manifest or work.root
        return self.issue_builder.path(
            target,
            rule,
            self.request.config,
            self.request.root,
            position,
        )
