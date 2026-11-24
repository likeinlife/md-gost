"""Shared helpers for the md-lint suite.

The linter is exercised through its CLI: that is the contract users and the
build rely on, and it is fast enough (no venv, no pandoc) to do it per test.
Unit tests import gost_lint directly where a rule is easier to pin down that way.
"""

import json
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

LintRun = tuple["subprocess.CompletedProcess[str]", list[dict[str, Any]]]

TOOL = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
REPO = TOOL.parents[1]


def run_lint(target: Path, *extra: str, cwd: Path = REPO) -> LintRun:
    """Run md-lint, return (CompletedProcess, parsed issues)."""
    command = _lint_command(target, extra)
    completed = subprocess.run(command, capture_output=True, text=True, cwd=cwd, check=False)
    assert completed.returncode in (0, 1), f"md-lint упал на {target}:\n{completed.stderr}"
    return completed, json.loads(completed.stdout)


def _lint_command(target: Path, extra: tuple[str, ...]) -> list[str]:
    command = [sys.executable, str(TOOL / "md_lint.py")]
    command.extend((str(target), "--format", "json"))
    command.extend(extra)
    return command


def rules_found(target: Path, *extra: str) -> set[str]:
    _, issues = run_lint(target, *extra)
    return {issue["rule"] for issue in issues}


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES


@pytest.fixture
def repo() -> Path:
    return REPO


@pytest.fixture
def sandbox(tmp_path: Path) -> Iterator[Path]:
    """A directory inside the repository — the config cascade needs a real path."""
    workdir = TOOL / ".pytest-sandbox"
    workdir.mkdir(exist_ok=True)
    target = workdir / tmp_path.name
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir()
    yield target
    shutil.rmtree(target, ignore_errors=True)
    if not any(workdir.iterdir()):
        workdir.rmdir()
