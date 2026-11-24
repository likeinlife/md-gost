"""Run the independent Markdown and OOXML linters at the build boundaries."""

import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path

from gost_builder.errors import BuildError

TOOLS = Path(__file__).resolve().parents[2]


def _command(source: str, module: str) -> list[str]:
    script = TOOLS / source
    if script.is_file():
        return [sys.executable, str(script)]
    return [sys.executable, "-P", "-m", module]


def _fail(text: str) -> None:
    raise BuildError(text)


def lint_markdown(src: Path, chapters: list[str]) -> None:
    """Skip Markdown lint when this checkout has no linter."""
    source = "md-gost-lint/md_lint.py"
    if not (TOOLS / source).is_file() and find_spec("gost_lint") is None:
        return
    sys.stdout.write("==> Pre-linting Markdown sources\n")
    sys.stdout.flush()
    command = _command(source, "gost_lint")
    targets = [str(src / chapter) for chapter in chapters]
    completed = subprocess.run(
        [*command, *targets],
        capture_output=True,
        text=True,
        check=False,
    )
    output = (completed.stdout + completed.stderr).strip()
    if output:
        sys.stdout.write(f"{output}\n")
        sys.stdout.flush()
    if completed.returncode == 1:
        _fail(
            "md-lint found errors (listed above). Fix them, or build with "
            "--no-lint to skip the check.",
        )
    if completed.returncode:
        _fail(f"md-lint failed to run (exit {completed.returncode})")


def lint_docx(output: Path) -> None:
    """Handle lint docx."""
    sys.stdout.write("==> Post-linting generated DOCX (OOXML)\n")
    sys.stdout.flush()
    command = _command(
        "md-gost-postlint/gost_docx_lint/post_lint.py",
        "gost_docx_lint.post_lint",
    )
    subprocess.run([*command, str(output)], check=True)
