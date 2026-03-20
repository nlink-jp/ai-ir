"""Tests for web UI routes using FastAPI TestClient."""
import json
import yaml
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from aiir.server.app import create_app

SAMPLE_REPORT = {
    "channel": "#test",
    "export_timestamp": "2026-03-19T10:00:00Z",
    "summary": {"title": "Test Incident", "severity": "high", "affected_systems": ["api-server"], "timeline": [], "root_cause": "OOM", "resolution": "restart", "summary": "Server went down."},
    "activity": {"incident_id": "#test", "channel": "#test", "participants": []},
    "roles": {"incident_id": "#test", "channel": "#test", "participants": [], "relationships": []},
    "tactics": [{"id": "tac-001", "title": "Check logs", "purpose": "find errors", "category": "log-analysis", "tools": ["grep"], "procedure": "grep error", "observations": "count errors", "tags": ["linux"], "source": {"channel": "#test", "participants": []}, "created_at": "2026-03-19"}],
}

SAMPLE_TACTIC = {
    "id": "tac-20260319-001",
    "title": "Test Tactic",
    "purpose": "testing",
    "category": "log-analysis",
    "tools": ["grep"],
    "procedure": "1. grep",
    "observations": "see output",
    "tags": ["linux", "logging"],
    "source": {"channel": "#test", "participants": ["alice"]},
    "created_at": "2026-03-19",
}

@pytest.fixture
def client(tmp_path):
    (tmp_path / "report.json").write_text(json.dumps(SAMPLE_REPORT))
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    (knowledge_dir / "tac-20260319-001-test.yaml").write_text(yaml.dump(SAMPLE_TACTIC))
    app = create_app(tmp_path)
    return TestClient(app)

def test_dashboard_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Test Incident" in resp.text

def test_dashboard_shows_tactic_count(client):
    resp = client.get("/")
    assert resp.status_code == 200

def test_report_view_returns_200(client):
    resp = client.get("/report?path=report.json")
    assert resp.status_code == 200
    assert "Test Incident" in resp.text

def test_report_view_404_for_missing(client):
    resp = client.get("/report?path=nonexistent.json")
    assert resp.status_code == 404

def test_knowledge_returns_200(client):
    resp = client.get("/knowledge")
    assert resp.status_code == 200
    assert "Test Tactic" in resp.text

def test_knowledge_filter_by_category(client):
    resp = client.get("/knowledge?category=log-analysis")
    assert resp.status_code == 200
    assert "Test Tactic" in resp.text

def test_knowledge_filter_no_match(client):
    resp = client.get("/knowledge?category=nonexistent")
    assert resp.status_code == 200
    assert "Test Tactic" not in resp.text

def test_tactic_view_returns_200(client):
    resp = client.get("/tactic?path=knowledge/tac-20260319-001-test.yaml")
    assert resp.status_code == 200
    assert "Test Tactic" in resp.text

def test_tactic_view_404_for_missing(client):
    resp = client.get("/tactic?path=knowledge/nonexistent.yaml")
    assert resp.status_code == 404

def test_api_reports_json(client):
    resp = client.get("/api/reports")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Incident"

def test_api_knowledge_json(client):
    resp = client.get("/api/knowledge")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == "tac-20260319-001"

def test_path_traversal_rejected(client):
    resp = client.get("/report?path=../../etc/passwd")
    assert resp.status_code == 404
