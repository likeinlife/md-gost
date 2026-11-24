"""Command-line interface for the document builder."""

import subprocess
import sys
from pathlib import Path

from gost_builder.errors import BuildError
from gost_builder.pipeline import build


def main(argv: list[str] | None = None) -> None:
    """Run the command."""
    arguments = sys.argv[1:] if argv is None else argv
    paths = [argument for argument in arguments if argument != "--no-lint"]
    if len(paths) != 1 or paths[0] in ("-h", "--help"):
        sys.exit("usage: md-gost build [--no-lint] <directory-with-markdown>")
    try:
        build(Path(paths[0]), lint_enabled="--no-lint" not in arguments)
    except (BuildError, subprocess.CalledProcessError) as exc:
        sys.exit(f"md-gost: {exc}")
