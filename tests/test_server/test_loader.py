"""Tests for server data loader."""
import json
import yaml
import pytest
from pathlib import Path
from aiir.server.loader import scan_reports, scan_tactics, load_report, load_tactic

SAMPLE_REPORT = {
    "channel": "#test",
    "export_timestamp": "2026-03-19T10:00:00Z",
    "summary": {"title": "Test Incident", "severity": "high", "affected_systems": [], "timeline": [], "root_cause": "", "resolution": "", "summary": "test"},
    "activity": {"incident_id": "#test", "channel": "#test", "participants": []},
    "roles": {"incident_id": "#test", "channel": "#test", "participants": [], "relationships": []},
    "tactics": [],
}

SAMPLE_TACTIC = {
    "id": "tac-20260319-001",
    "title": "Test Tactic",
    "purpose": "testing",
    "category": "log-analysis",
    "tools": ["grep"],
    "procedure": "1. do thing",
    "observations": "see result",
    "tags": ["test"],
    "source": {"channel": "#test", "participants": ["alice"]},
    "created_at": "2026-03-19",
}

@pytest.fixture
def data_dir(tmp_path):
    # Write sample report
    (tmp_path / "report.json").write_text(json.dumps(SAMPLE_REPORT))
    # Write a non-report JSON (should be ignored)
    (tmp_path / "other.json").write_text('{"foo": "bar"}')
    # Write sample tactic
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    (knowledge_dir / "tac-20260319-001-test.yaml").write_text(yaml.dump(SAMPLE_TACTIC))
    return tmp_path

def test_scan_reports_finds_report(data_dir):
    reports = scan_reports(data_dir)
    assert len(reports) == 1
    assert reports[0]["summary"]["title"] == "Test Incident"

def test_scan_reports_ignores_non_reports(data_dir):
    reports = scan_reports(data_dir)
    assert all("summary" in r and "tactics" in r for r in reports)

def test_scan_tactics_finds_tactic(data_dir):
    tactics = scan_tactics(data_dir)
    assert len(tactics) == 1
    assert tactics[0]["id"] == "tac-20260319-001"

def test_load_report_success(data_dir):
    report = load_report(data_dir, "report.json")
    assert report is not None
    assert report["summary"]["title"] == "Test Incident"

def test_load_report_path_traversal(data_dir, tmp_path):
    # Attempt path traversal
    result = load_report(data_dir, "../../etc/passwd")
    assert result is None

def test_load_tactic_success(data_dir):
    tactic = load_tactic(data_dir, "knowledge/tac-20260319-001-test.yaml")
    assert tactic is not None
    assert tactic["id"] == "tac-20260319-001"

def test_load_tactic_path_traversal(data_dir):
    result = load_tactic(data_dir, "../../etc/shadow")
    assert result is None

def test_scan_reports_adds_metadata(data_dir):
    reports = scan_reports(data_dir)
    assert "_filename" in reports[0]
    assert "_path" in reports[0]

def test_scan_tactics_adds_metadata(data_dir):
    tactics = scan_tactics(data_dir)
    assert "_filename" in tactics[0]
    assert "_path" in tactics[0]
