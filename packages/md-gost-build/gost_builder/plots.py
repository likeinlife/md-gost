"""Execute a document plot block and save its Matplotlib figure."""

import importlib
import runpy
import sys
import traceback
from pathlib import Path
from typing import Any

PNG_DPI = 300
IDEF0_PACKAGE = "idef0"


def _load_plot_modules() -> tuple[Any, Any]:
    try:
        return _import_pyplot_and_seaborn()
    except ImportError:
        sys.exit("md-gost: .plot and .idef0 require the optional dependencies from .[plots]")


def _import_pyplot_and_seaborn() -> tuple[Any, Any]:
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    return (
        importlib.import_module("matplotlib.pyplot"),
        importlib.import_module("seaborn"),
    )


def _figure_from_namespace(namespace: dict[str, Any], pyplot: Any) -> Any:
    if "diagram" in namespace:
        if namespace.get("fig") is not None or namespace.get("g") is not None:
            message = "define either diagram or fig/g, not both"
            raise ValueError(message)
        return namespace[IDEF0_PACKAGE].draw(namespace.get("diagram"))
    figure = namespace.get("fig")
    if figure is None:
        figure = namespace.get("g")
    if figure is None:
        return pyplot.gcf()
    if hasattr(figure, "savefig"):
        return figure
    return getattr(figure, "figure", pyplot.gcf())


def _run_source(source: Path, namespace: dict[str, Any]) -> dict[str, Any]:
    try:
        return runpy.run_path(str(source), init_globals=namespace)
    except Exception:
        traceback.print_exc()
        sys.exit(f"md-gost: failed to render plot source {source}")


def _figure_from_source(source: Path) -> Any:
    pyplot, seaborn = _load_plot_modules()
    idef0 = importlib.import_module(IDEF0_PACKAGE)
    if source.suffix.lower() == ".idef0":
        try:
            return idef0.draw(idef0.parse_text(source.read_text(encoding="utf-8")))
        except idef0.ModelError as exc:
            sys.exit(f"{source}: {exc}")
    namespace = {"plt": pyplot, "sns": seaborn, IDEF0_PACKAGE: idef0}
    return _figure_from_namespace(_run_source(source, namespace), pyplot)


def render(source: Path, target: Path) -> None:
    """Handle render."""
    figure = _figure_from_source(source)
    image_format = target.suffix.lstrip(".")
    figure.savefig(target, format=image_format, dpi=PNG_DPI, bbox_inches="tight")


def _parse_paths(arguments: list[str]) -> tuple[Path, Path]:
    expected_arguments = 3
    if len(arguments) != expected_arguments:
        sys.exit("usage: plots.py <source.py|source.idef0> <output.png|output.svg>")
    return Path(arguments[1]), Path(arguments[2])


if __name__ == "__main__":
    # A standalone builder checkout can use the sibling IDEF0 source package.
    idef0_source = Path(__file__).resolve().parents[2] / IDEF0_PACKAGE
    if (idef0_source / IDEF0_PACKAGE / "__init__.py").is_file():
        sys.path.insert(0, str(idef0_source))
    plot_source, plot_target = _parse_paths(sys.argv)
    render(plot_source, plot_target)
