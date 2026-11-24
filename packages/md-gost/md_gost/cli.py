"""Compose lint, format, build, postlint, and lsp into one command."""

import subprocess
import sys
from pathlib import Path
from typing import Annotated, Literal

import typer

from gost_builder.errors import BuildError
from gost_builder.pipeline import build as assemble
from gost_docx_lint import check as check_docx
from gost_lint.cli import FIXABLE, PATHS_HELP, LintRequest, run_lint
from gost_lint.format_run import Session
from gost_lint.lsp.cli import main as start_lsp

Report = Literal["text", "json"]
HELP_NAMES = ("-h", "--help")
app = typer.Typer(
    name="md-gost",
    help="Сборка, проверка и форматирование Markdown учебных работ.",
    no_args_is_help=True,
    add_completion=False,
    pretty_exceptions_enable=False,
    context_settings={"help_option_names": list(HELP_NAMES)},
)
_FIXABLE_NAMES = ", ".join(FIXABLE)
FIX_HELP = f"исправить механическое ({_FIXABLE_NAMES})"
PATHS = typer.Argument(None, help=PATHS_HELP)


def _paths(paths: list[Path] | None) -> list[Path]:
    if paths is None:
        return []
    return list(paths)


@app.command()
def lint(
    paths: list[Path] | None = PATHS,
    output_format: Annotated[
        Report,
        typer.Option("--format", help="формат отчёта"),
    ] = "text",
    rules: Annotated[
        str,
        typer.Option("--rules", help="только эти правила, через запятую"),
    ] = "",
    ignore: Annotated[
        str,
        typer.Option("--ignore", help="пропустить эти правила, через запятую"),
    ] = "",
    strict: Annotated[
        bool,
        typer.Option("--strict", help="считать предупреждения ошибками"),
    ] = False,
    fix: Annotated[bool, typer.Option("--fix", help=FIX_HELP)] = False,
    no_config: Annotated[
        bool,
        typer.Option("--no-config", help="игнорировать mdlint.toml"),
    ] = False,
    list_rules: Annotated[
        bool,
        typer.Option("--list-rules", help="показать правила и их уровни"),
    ] = False,
    no_color: Annotated[
        bool,
        typer.Option("--no-color", help="без цвета в отчёте"),
    ] = False,
) -> None:
    """Проверить главы и диаграммы."""
    request = LintRequest(
        _paths(paths),
        output_format,
        rules,
        ignore,
        strict,
        fix,
        no_config,
        no_color,
    )
    code = run_lint(request, listing=list_rules)
    if code:
        raise typer.Exit(code)


@app.command(name="format")
def format_sources(
    paths: list[Path] | None = PATHS,
    check: Annotated[
        bool,
        typer.Option("--check", help="не записывать файлы; код 1, если есть правки"),
    ] = False,
    diff: Annotated[
        bool,
        typer.Option("--diff", help="показать diff и не записывать файлы"),
    ] = False,
) -> None:
    """Выровнять таблицы и убрать лишние пробелы."""
    code = Session(_paths(paths), checking=check, showing_diff=diff).run()
    if code:
        raise typer.Exit(code)


@app.command()
def build(
    directory: Annotated[Path, typer.Argument(help="каталог с book.toml")],
    no_lint: Annotated[
        bool,
        typer.Option("--no-lint", help="не проверять главы перед сборкой"),
    ] = False,
) -> None:
    """Собрать ГОСТ-.docx из Markdown."""
    try:
        assemble(directory, lint_enabled=not no_lint)
    except (BuildError, subprocess.CalledProcessError) as exc:
        sys.stderr.write(f"md-gost: {exc}\n")
        raise typer.Exit(1) from exc


@app.command()
def postlint(document: Annotated[Path, typer.Argument(help="готовый .docx")]) -> None:
    """Проверить OOXML собранного документа."""
    raise typer.Exit(check_docx(document))


@app.command()
def lsp() -> None:
    """Запустить языковой сервер по stdio."""
    start_lsp()


def main(argv: list[str] | None = None) -> None:
    """Entry point for the md-gost console script."""
    app(args=argv, prog_name="md-gost")
