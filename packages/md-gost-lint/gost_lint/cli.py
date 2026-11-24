"""Command-line argument parsing and lint command orchestration."""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from gost_lint.config import Chain
from gost_lint.fixes import FIXABLE, apply_fixes
from gost_lint.paths import repository_root
from gost_lint.report import Issue, json_report, summary, text_report
from gost_lint.rules.registry import Rule
from gost_lint.rules.registry import load_all as load_rules
from gost_lint.runner import RuleRun, RuleRunner
from gost_lint.targets import Targets

STORE_TRUE = "store_true"
NO_CONFIG_OPTION = "--no-config"
USAGE_ERROR = 2
PATHS_HELP = "файлы .md или каталоги работ (по умолчанию — репозиторий)"


@dataclass(frozen=True)
class LintRequest:
    """Flags shared by `md-lint` and `md-gost lint`."""

    paths: list[Path]
    output_format: str
    rules: str
    ignore: str
    strict: bool
    fix: bool
    no_config: bool
    no_color: bool


class Options:
    """Create parser and validate rule selection options."""

    def parser(self) -> argparse.ArgumentParser:
        """Build the command-line parser."""
        parser = argparse.ArgumentParser(
            prog="md-lint",
            description=(__doc__ or "").splitlines()[0],
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        self._add_arguments(parser)
        return parser

    def parse_rules(self, rule_text: str) -> set[str]:
        """Parse rules."""
        return {part.strip() for part in rule_text.split(",") if part.strip()}

    def list_rules(self, rules: dict[str, Rule]) -> int:
        """List rules."""
        for rule in sorted(rules.values(), key=lambda candidate: candidate.id):
            self._write_rule(rule)
        return 0

    def _add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("paths", nargs="*", type=Path, help=PATHS_HELP)
        parser.add_argument(
            "--format",
            dest="output_format",
            choices=("text", "json"),
            default="text",
        )
        parser.add_argument(
            "--rules",
            default="",
            help="проверять только эти правила, через запятую",
        )
        parser.add_argument("--ignore", default="", help="пропустить эти правила, через запятую")
        parser.add_argument("--strict", action=STORE_TRUE, help="считать предупреждения ошибками")
        names = ", ".join(FIXABLE)
        parser.add_argument("--fix", action=STORE_TRUE, help=f"исправить механическое ({names})")
        parser.add_argument(
            NO_CONFIG_OPTION,
            action=STORE_TRUE,
            help="игнорировать mdlint.toml (уровни по умолчанию)",
        )
        parser.add_argument("--list-rules", action=STORE_TRUE)
        parser.add_argument("--no-color", action=STORE_TRUE)

    def _write_rule(self, rule: Rule) -> None:
        rule_id = rule.id.ljust(10)
        level = rule.level.ljust(8)
        line = f"{rule_id} {level} {rule.summary}\n"
        sys.stdout.write(line)


class RuleSelection:
    """Validate positive and ignored rule filters together."""

    def __init__(self, selected: set[str], ignored: set[str]) -> None:
        """Initialize the instance."""
        self.selected = selected
        self.ignored = ignored

    def validate(self, rules: dict[str, Rule]) -> None:
        """Handle validate."""
        unknown = (self.selected | self.ignored) - set(rules)
        if unknown:
            names = ", ".join(sorted(unknown))
            sys.exit(f"md-lint: неизвестные правила: {names}")


class CommandContext:
    """Resolved paths and configuration shared by command steps."""

    def __init__(self, requested_paths: list[Path], *, use_config: bool) -> None:
        """Initialize the instance."""
        self.targets = Targets()
        current = Path.cwd()
        self.root = repository_root(current) or current
        self.paths = requested_paths or [self.root]
        self.config = Chain(self.root, enabled=use_config)
        self.works = self.targets.collect_works(self.paths, self.root)


class Command:
    """Run the selected lint operation and render its report."""

    def __init__(self, request: LintRequest, rules: dict[str, Rule]) -> None:
        """Initialize the instance."""
        self.request = request
        self.rules = rules
        self.options = Options()
        self.context = CommandContext(request.paths, use_config=not request.no_config)

    def run(self) -> int:
        """Handle run."""
        if self._report_target_errors():
            return USAGE_ERROR
        if not self._has_lintable_content():
            return 0
        selection = RuleSelection(
            self.options.parse_rules(self.request.rules),
            self.options.parse_rules(self.request.ignore),
        )
        selection.validate(self.rules)
        self._apply_fixes(selection)
        return self._lint(selection)

    def _report_target_errors(self) -> bool:
        problems = self.context.targets.check_targets(self.context.paths)
        for problem in problems:
            sys.stderr.write(f"md-lint: {problem}\n")
        return bool(problems)

    def _has_lintable_content(self) -> bool:
        if any(work.docs or work.diagrams for work in self.context.works):
            return True
        listed = ", ".join(str(path) for path in self.context.paths)
        sys.stderr.write(f"md-lint: проверять нечего — в {listed} нет файлов .md\n")
        return False

    def _apply_fixes(self, selection: RuleSelection) -> None:
        if not self.request.fix:
            return
        selected = (selection.selected or set(FIXABLE)) - selection.ignored
        changed = apply_fixes(self.context.works, self.context.config, selected)
        sys.stdout.write(f"md-lint: исправлено файлов — {len(changed)}\n")
        for relative_path in changed:
            sys.stdout.write(f"  {relative_path}\n")
        self.context.works = self.context.targets.collect_works(
            self.context.paths,
            self.context.root,
        )

    def _lint(self, selection: RuleSelection) -> int:
        request = RuleRun(
            self.context.works,
            self.rules,
            self.context.config,
            self.context.root,
            selection.selected,
            selection.ignored,
        )
        issues = RuleRunner(request).run()
        self._write_report(issues)
        return 1 if any(issue.level == "error" for issue in issues) else 0

    def _write_report(self, issues: list[Issue]) -> None:
        if self.request.strict:
            for issue in issues:
                issue.level = "error"
        if self.request.output_format == "json":
            sys.stdout.write(f"{json_report(issues)}\n")
            return
        if issues:
            color = not self.request.no_color and sys.stdout.isatty()
            sys.stdout.write(f"{text_report(issues, color=color)}\n")
        sys.stdout.write(f"{summary(issues)}\n")


def run_lint(request: LintRequest, *, listing: bool) -> int:
    """Run rule listing or a lint pass. Shared by `md-lint` and `md-gost lint`."""
    rules = load_rules()
    if listing:
        return Options().list_rules(rules)
    return Command(request, rules).run()


def run_cli(argv: list[str] | None = None) -> int:
    """Run cli."""
    options = Options()
    args = options.parser().parse_args(argv)
    request = LintRequest(
        paths=list(args.paths),
        output_format=args.output_format,
        rules=args.rules,
        ignore=args.ignore,
        strict=args.strict,
        fix=args.fix,
        no_config=args.no_config,
        no_color=args.no_color,
    )
    return run_lint(request, listing=args.list_rules)
