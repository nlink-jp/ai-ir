"""Scan directories and load ai-ir output files."""
from pathlib import Path
import json
import yaml


def scan_reports(data_dir: Path) -> list[dict]:
    """Find and load all full report JSON files in data_dir (recursive)."""
    reports = []
    for path in sorted(data_dir.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "summary" in data and "tactics" in data:
                data["_filename"] = path.name
                data["_path"] = str(path.relative_to(data_dir))
                reports.append(data)
        except Exception:
            continue
    return reports


def scan_tactics(data_dir: Path) -> list[dict]:
    """Find and load all tactic YAML files in data_dir (recursive)."""
    tactics = []
    for path in sorted(data_dir.rglob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and str(data.get("id", "")).startswith("tac-"):
                data["_filename"] = path.name
                data["_path"] = str(path.relative_to(data_dir))
                tactics.append(data)
        except Exception:
            continue
    return tactics


def load_report(data_dir: Path, rel_path: str) -> dict | None:
    """Load a single report by its relative path. Prevents path traversal."""
    try:
        target = (data_dir / rel_path).resolve()
        if not str(target).startswith(str(data_dir.resolve())):
            return None  # path traversal attempt
        data = json.loads(target.read_text(encoding="utf-8"))
        if "summary" in data and "tactics" in data:
            return data
    except Exception:
        pass
    return None


def load_tactic(data_dir: Path, rel_path: str) -> dict | None:
    """Load a single tactic YAML by its relative path. Prevents path traversal."""
    try:
        target = (data_dir / rel_path).resolve()
        if not str(target).startswith(str(data_dir.resolve())):
            return None
        data = yaml.safe_load(target.read_text(encoding="utf-8"))
        if isinstance(data, dict) and str(data.get("id", "")).startswith("tac-"):
            return data
    except Exception:
        pass
    return None
