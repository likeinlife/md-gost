"""Render the manifest's chapters using Pandoc and the bundled Lua filter."""

import os
import subprocess
import sys
from pathlib import Path

from gost_builder.manifest import Manifest
from gost_builder.plantuml_cmd import PlantUML
from gost_builder.reference.template import style_reference

PACKAGE = Path(__file__).resolve().parent
GENERATED_IMAGES = (
    "diagram_*.puml",
    "diagram_*.png",
    "diagram_*.svg",
    "plot_*.py",
    "plot_*.idef0",
    "plot_*.png",
    "plot_*.svg",
)


def _image_directory(work: Path) -> Path:
    images = work / "img"
    images.mkdir(parents=True, exist_ok=True)
    for pattern in GENERATED_IMAGES:
        for generated in images.glob(pattern):
            generated.unlink()
    return images


def _reference(pandoc: str, work: Path) -> Path:
    reference = work / "reference.docx"
    with reference.open("wb") as target:
        subprocess.run(
            [pandoc, "--print-default-data-file", "reference.docx"],
            stdout=target,
            check=True,
        )
    style_reference(reference)
    return reference


def _filter_environment(
    images: Path,
    manifest: Manifest,
    plantuml: PlantUML | None,
) -> dict[str, str]:
    environment = {
        **os.environ,
        "MD2GOST_IMG_DIR": str(images),
        "MD2GOST_NUMBER_SECTIONS": "1" if manifest.number_sections else "0",
        "MD2GOST_IMAGE_FORMAT": "svg" if manifest.prefer_vector else "png",
        "MD2GOST_PYTHON": sys.executable,
        "MD2GOST_PLOT_RENDERER": str(PACKAGE / "plots.py"),
    }
    if plantuml is not None:
        environment.update(plantuml.environment())
    return environment


def render(pandoc: str, src: Path, manifest: Manifest, plantuml: PlantUML | None) -> Path:
    """Handle render."""
    work = src / ".md-to-gost"
    images = _image_directory(work)
    sys.stdout.write("==> Generating GOST reference template\n")
    reference = _reference(pandoc, work)
    output = (src / manifest.output).resolve()
    arguments = [
        pandoc,
        "--from=markdown",
        "--to=docx",
        "--output",
        str(output),
        "--syntax-highlighting=none",
        "--lua-filter",
        str(PACKAGE / "filters" / "plantuml.lua"),
        "--reference-doc",
        str(reference),
    ]
    if manifest.toc:
        arguments.extend(["--toc", "--toc-depth=2", "--metadata", "toc-title=Содержание"])
    arguments.extend(str(src / chapter) for chapter in manifest.chapters)
    sys.stdout.write("==> Running pandoc\n")
    subprocess.run(
        arguments,
        cwd=src,
        env=_filter_environment(images, manifest, plantuml),
        check=True,
    )
    return output
