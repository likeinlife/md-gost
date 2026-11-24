"""Run md-lint with the active Python interpreter."""

import sys

from gost_lint.cli import run_cli

if __name__ == "__main__":
    sys.exit(run_cli())
