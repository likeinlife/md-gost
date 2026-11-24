"""Launch the optional language server over stdio."""

import sys
from importlib.util import find_spec


def main() -> None:
    """Run the command."""
    if find_spec("pygls") is None:
        sys.exit("md-gost lsp: установите поддержку LSP: uv tool install '.[lsp]'")
    from gost_lint.lsp.server import server

    server.start_io()
