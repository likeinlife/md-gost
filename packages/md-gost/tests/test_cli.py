"""The entry command delegates to the lint, format, and postlint tools."""

import os
import subprocess
import sys
from pathlib import Path

from conftest import ENTRY, LINT, REPO, TOOLS

NO_CONFIG = "--no-config"
USAGE_ERROR = 2
UTF8 = "utf-8"
LINT_COMMAND = "lint"
FORMAT = "format"
CHAPTER = "chapter.md"
COMMANDS = (LINT_COMMAND, FORMAT, "build", "postlint", "lsp")
ROOTS = (ENTRY, LINT, TOOLS / "md-gost-build", TOOLS / "md-gost-postlint")


def gost(*args: str | Path) -> "subprocess.CompletedProcess[str]":
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(str(path) for path in ROOTS)
    command = [sys.executable, "-m", "md_gost"]
    command.extend(str(arg) for arg in args)
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=REPO,
        env=env,
        check=False,
    )


def legacy(*args: str) -> "subprocess.CompletedProcess[str]":
    command = [sys.executable, str(LINT / "md_lint.py"), *args]
    return subprocess.run(command, capture_output=True, text=True, cwd=REPO, check=False)


class TestCommands:
    def test_help_lists_subcommands(self) -> None:
        completed = gost("--help")
        assert completed.returncode == 0
        for name in COMMANDS:
            assert name in completed.stdout

    def test_postlint_requires_a_docx(self, sandbox: Path) -> None:
        completed = gost("postlint", sandbox / "missing.docx")
        assert completed.returncode == USAGE_ERROR
        assert "docx" in completed.stderr


class TestLint:
    def test_report_matches_library_cli(self, fixtures: Path) -> None:
        target = str(fixtures / "style.md")
        modern = gost(LINT_COMMAND, target, NO_CONFIG, "--format", "json")
        previous = legacy(target, NO_CONFIG, "--format", "json")
        assert modern.returncode == previous.returncode == 1
        assert modern.stdout == previous.stdout

    def test_list_rules_matches_library_cli(self) -> None:
        modern = gost(LINT_COMMAND, "--list-rules")
        previous = legacy("--list-rules")
        assert modern.returncode == previous.returncode == 0
        assert modern.stdout == previous.stdout

    def test_fix_repairs_heading_dot(self, fixtures: Path, sandbox: Path) -> None:
        target = sandbox / "headings.md"
        target.write_text((fixtures / "headings.md").read_text(encoding=UTF8), encoding=UTF8)
        completed = gost(LINT_COMMAND, target, "--fix", NO_CONFIG)
        assert completed.returncode != USAGE_ERROR
        text = target.read_text(encoding=UTF8)
        assert "## 1 Первый раздел" in text
        assert "### 1.1 Подраздел с номером" in text
        assert "## Заключение" in text

    def test_unknown_rule_is_rejected(self, fixtures: Path) -> None:
        completed = gost(LINT_COMMAND, fixtures / "clean.md", "--rules", "NOPE001")
        assert completed.returncode != 0
        assert "NOPE001" in completed.stdout + completed.stderr

    def test_missing_path_is_an_error(self, sandbox: Path) -> None:
        completed = gost(LINT_COMMAND, sandbox / "nope.md")
        assert completed.returncode == USAGE_ERROR
        assert "путь не найден" in completed.stderr


class TestFormat:
    def test_writes_tables_and_spaces(self, sandbox: Path) -> None:
        target = sandbox / CHAPTER
        source = "# Глава\n\nТекст  после.\n\n|A|B|\n|---|---|\n|x|два|\n"
        target.write_text(source, encoding=UTF8)
        completed = gost(FORMAT, target)
        assert completed.returncode == 0
        assert "отформатировано файлов — 1" in completed.stdout
        text = target.read_text(encoding=UTF8)
        assert "Текст после." in text
        assert "| A   | B   |" in text

    def test_second_pass_is_clean(self, sandbox: Path) -> None:
        target = sandbox / CHAPTER
        target.write_text("# Глава\n\nТекст  после.\n", encoding=UTF8)
        assert gost(FORMAT, target).returncode == 0
        checked = gost(FORMAT, "--check", target)
        assert checked.returncode == 0
        assert "без изменений — 1" in checked.stdout

    def test_check_does_not_write(self, sandbox: Path) -> None:
        target = sandbox / CHAPTER
        source = "# Глава\n\nТекст  после.\n"
        target.write_text(source, encoding=UTF8)
        checked = gost(FORMAT, "--check", target)
        assert checked.returncode == 1
        assert target.read_text(encoding=UTF8) == source
        assert "требуется форматирование — 1" in checked.stdout

    def test_diff_does_not_write(self, sandbox: Path) -> None:
        target = sandbox / CHAPTER
        source = "# Глава\n\nТекст  после.\n"
        target.write_text(source, encoding=UTF8)
        diff = gost(FORMAT, "--diff", target)
        assert diff.returncode == 1
        assert "Текст после." in diff.stdout
        assert target.read_text(encoding=UTF8) == source

    def test_leaves_heading_numbers(self, sandbox: Path) -> None:
        target = sandbox / CHAPTER
        source = "# Глава\n\n## 3.1. Название\n\nТекст.\n"
        target.write_text(source, encoding=UTF8)
        assert gost(FORMAT, target).returncode == 0
        assert "## 3.1. Название" in target.read_text(encoding=UTF8)

    def test_keeps_crlf(self, sandbox: Path) -> None:
        target = sandbox / CHAPTER
        source = "# Глава\r\n\r\nТекст  после.\r\n"
        target.write_bytes(source.encode(UTF8))
        assert gost(FORMAT, target).returncode == 0
        assert target.read_bytes() == "# Глава\r\n\r\nТекст после.\r\n".encode()

    def test_rejects_a_missing_path(self, sandbox: Path) -> None:
        completed = gost(FORMAT, sandbox / "nope.md")
        assert completed.returncode == USAGE_ERROR
        assert "путь не найден" in completed.stderr
