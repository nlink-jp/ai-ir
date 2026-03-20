"""Load and validate scat/stail JSON export files."""

import json
from pathlib import Path

from aiir.models import SlackExport


def load_export(path: Path) -> SlackExport:
    """Load and validate a scat/stail JSON export file.

    Args:
        path: Path to the JSON export file.

    Returns:
        Validated SlackExport instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        pydantic.ValidationError: If the JSON does not match the expected schema.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return SlackExport.model_validate(data)


def load_export_from_string(content: str) -> SlackExport:
    """Load and validate from a JSON string.

    Args:
        content: JSON string containing the export data.

    Returns:
        Validated SlackExport instance.

    Raises:
        json.JSONDecodeError: If the content is not valid JSON.
        pydantic.ValidationError: If the JSON does not match the expected schema.
    """
    data = json.loads(content)
    return SlackExport.model_validate(data)
