#!/usr/bin/env python3
"""Run the Markdown linter directly from a checkout."""

import sys

from gost_lint.cli import run_cli

if __name__ == "__main__":
    sys.exit(run_cli())
