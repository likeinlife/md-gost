"""Generate the editor schema for book.toml from the manifest configuration."""

import json
from dataclasses import MISSING, fields
from pathlib import Path
from types import MappingProxyType
from typing import Any

from gost_builder.frame.settings import DEFAULTS
from gost_builder.manifest import Manifest

TYPE = "type"
SCALAR_TYPES: MappingProxyType[Any, str] = MappingProxyType({str: "string", bool: "boolean"})
SCHEMA_PATH = Path(__file__).resolve().parent / "book.schema.json"


def make_schema() -> dict[str, Any]:
    """Describe supported manifest fields and their actual defaults."""
    properties: dict[str, Any] = {}
    required = []
    for manifest_field in fields(Manifest):
        name = manifest_field.name
        schema: dict[str, Any] = {"description": manifest_field.metadata["description"]}
        if name == "chapters":
            schema.update({TYPE: "array", "items": {TYPE: "string"}, "minItems": 1})
        elif name == "frame":
            schema["oneOf"] = [{TYPE: "boolean"}, _frame_schema()]
        else:
            schema[TYPE] = SCALAR_TYPES[manifest_field.type]
        if manifest_field.default is MISSING:
            required.append(name)
        else:
            schema["default"] = manifest_field.default
        properties[name] = schema
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Манифест book.toml",
        "description": "Настройки сборки документа md-to-gost.",
        TYPE: "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def _frame_schema() -> dict[str, Any]:
    properties: dict[str, Any] = {}
    for name, default in DEFAULTS.items():
        properties[name] = {TYPE: ["string", "integer"], "default": default}
    return {TYPE: "object", "properties": properties, "additionalProperties": False}


if __name__ == "__main__":
    SCHEMA_PATH.write_text(
        f"{json.dumps(make_schema(), ensure_ascii=False, indent=2)}\n",
        encoding="utf-8",
    )
