"""CLI behaviour: exit codes, output formats, --fix."""

import subprocess
import sys
from pathlib import Path

from conftest import REPO, TOOL, rules_found, run_lint

NO_CONFIG = "--no-config"
USAGE_ERROR = 2
UTF8 = "utf-8"
TYPO_FILE = "typo.md"
FIX = "--fix"
HEADINGS_FILE = "headings.md"


def cli(*args: str) -> "subprocess.CompletedProcess[str]":
    command = [sys.executable, str(TOOL / "md_lint.py")]
    command.extend(args)
    return subprocess.run(command, capture_output=True, text=True, cwd=REPO, check=False)


def test_module_cli_uses_only_stdlib() -> None:
    command = [sys.executable, "-E", "-S", "-m", "gost_lint", "--list-rules"]
    completed = subprocess.run(command, capture_output=True, text=True, cwd=TOOL, check=True)
    assert completed.stdout == cli("--list-rules").stdout


class TestGroup1:
    def test_clean_file_exits_zero(self, fixtures: Path) -> None:
        assert cli(str(fixtures / "clean.md"), NO_CONFIG).returncode == 0

    def test_errors_exit_one(self, fixtures: Path) -> None:
        assert cli(str(fixtures / "style.md"), NO_CONFIG).returncode == 1

    def test_warnings_alone_exit_zero(self, fixtures: Path) -> None:
        """typo.md holds errors (TYPO004, TYPO006), so check a warning-only fixture."""
        completed = cli(str(fixtures / TYPO_FILE), NO_CONFIG, "--ignore", "TYPO004,TYPO006")
        assert completed.returncode == 0

    def test_strict_promotes_warnings(self, fixtures: Path) -> None:
        args = (NO_CONFIG, "--ignore", "TYPO004,TYPO006", "--strict")
        completed = cli(str(fixtures / TYPO_FILE), *args)
        assert completed.returncode == 1

    def test_rules_filter(self, fixtures: Path) -> None:
        assert rules_found(fixtures / "style.md", NO_CONFIG, "--rules", "STYLE001") == {"STYLE001"}

    def test_unknown_rule_is_rejected(self, fixtures: Path) -> None:
        completed = cli(str(fixtures / "clean.md"), "--rules", "NOPE001")
        assert completed.returncode != 0
        assert "NOPE001" in completed.stdout + completed.stderr


class TestGroup2:
    def test_list_rules_covers_every_group(
        self,
    ) -> None:
        completed = cli("--list-rules")
        assert completed.returncode == 0
        for group in ("STRUCT", "REF", "BIB", "STYLE", "TYPO", "BUILD"):
            assert group in completed.stdout

    def test_json_report_shape(self, fixtures: Path) -> None:
        _, issues = run_lint(fixtures / "style.md", NO_CONFIG)
        assert issues
        for issue in issues:
            assert set(issue) == {"path", "line", "column", "level", "rule", "message"}
            assert issue["level"] in ("error", "warning")
            assert issue["line"] >= 1

    def test_fix_repairs_mechanical_only(self, fixtures: Path, sandbox: Path) -> None:
        target = sandbox / TYPO_FILE
        target.write_text((fixtures / TYPO_FILE).read_text(encoding=UTF8), encoding=UTF8)
        cli(str(target), FIX, NO_CONFIG)
        after = rules_found(target, NO_CONFIG)

        assert {"TYPO001", "TYPO002", "TYPO003", "TYPO005"} & after == set()
        assert {"TYPO004", "TYPO006"} <= after
        text = target.read_text(encoding=UTF8)
        assert "дефис — вместо тире, «прямые кавычки»" in text
        assert "сиcтема" in text
        for line in (fixtures / TYPO_FILE).read_text(encoding=UTF8).splitlines():
            if line.lstrip()[:1] in "—–":
                assert line in text.splitlines()

    def test_repository_lints_without_crashing(self, repo: Path) -> None:
        """The repository sources: findings are expected, an exception is not."""
        run_lint(repo)

    def test_fix_leaves_formulas_alone(self, sandbox: Path) -> None:
        """LaTeX — это разметка: пробелы в ней правит автор, а не линтер."""
        source = "# Глава 1. Тест\n\n$$\na  =  b ,\n$$\n\nТекст  после.\n"
        target = sandbox / "formula.md"
        target.write_text(source, encoding=UTF8)

        cli(str(target), "--fix", NO_CONFIG)

        fixed = target.read_text(encoding=UTF8)
        assert "a  =  b ," in fixed, "автофикс залез внутрь формулы"
        assert "Текст после." in fixed, "за пределами формулы пробелы не поправились"

    def test_fix_section_number_dot(self, fixtures: Path, sandbox: Path) -> None:
        target = sandbox / HEADINGS_FILE
        target.write_text((fixtures / HEADINGS_FILE).read_text(encoding=UTF8), encoding=UTF8)
        assert "STRUCT008" in rules_found(target, NO_CONFIG)

        cli(str(target), FIX, NO_CONFIG)
        assert "STRUCT008" not in rules_found(target, NO_CONFIG)

        text = target.read_text(encoding=UTF8)
        assert "## 1 Первый раздел" in text
        assert "### 1.1 Подраздел с номером" in text

    def test_fix_keeps_structural_titles(self, fixtures: Path, sandbox: Path) -> None:
        target = sandbox / HEADINGS_FILE
        source = (fixtures / HEADINGS_FILE).read_text(encoding=UTF8)
        target.write_text(source, encoding=UTF8)
        cli(str(target), FIX, NO_CONFIG)
        text = target.read_text(encoding=UTF8)
        assert "# Лабораторная работа № 2" in text, "заголовок без номера не трогаем"
        assert "## Заключение" in text, "у структурного элемента номер снимается целиком"


class TestGroup3:
    def test_missing_path_is_an_error(self, sandbox: Path) -> None:
        """A typo in the path must not look like a clean run."""
        completed = cli(str(sandbox / "nope.md"))
        assert completed.returncode == USAGE_ERROR
        assert "путь не найден" in completed.stderr

    def test_non_markdown_file_is_rejected(self, repo: Path) -> None:
        completed = cli(str(repo / "mdlint.toml"))
        assert completed.returncode == USAGE_ERROR
        assert "проверять можно только" in completed.stderr

    def test_empty_directory_says_so(self, sandbox: Path) -> None:
        completed = cli(str(sandbox))
        assert completed.returncode == 0
        assert "проверять нечего" in completed.stderr
