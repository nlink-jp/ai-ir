"""Tests for report.generator module."""
from __future__ import annotations

from aiir.report.generator import generate_json_report, generate_markdown_report, make_incident_id
from aiir.models import (
    Action,
    ActivityAnalysis,
    IncidentSummary,
    ParticipantActivity,
    ParticipantRole,
    ProcessedExport,
    ProcessedMessage,
    Relationship,
    RoleAnalysis,
    Tactic,
    TacticSource,
    TimelineEvent,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_export() -> ProcessedExport:
    msg = ProcessedMessage(
        user_id="U001",
        user_name="alice",
        post_type="user",
        timestamp="2026-03-19T09:55:00Z",
        timestamp_unix="1742378100.000000",
        text="server is down",
    )
    return ProcessedExport(
        export_timestamp="2026-03-19T10:00:00Z",
        channel_name="#incident-test",
        messages=[msg],
        security_warnings=[],
    )


def _make_summary() -> IncidentSummary:
    return IncidentSummary(
        title="API Server Outage",
        severity="high",
        affected_systems=["api-server"],
        timeline=[TimelineEvent(timestamp="09:55", actor="alice", event="alert triggered")],
        root_cause="OOM kill",
        resolution="Pod restarted",
        summary="Server went down due to OOM.",
    )


def _make_activity() -> ActivityAnalysis:
    return ActivityAnalysis(
        incident_id="#incident-test",
        channel="#incident-test",
        participants=[
            ParticipantActivity(
                user_name="alice",
                role_hint="Lead Responder",
                actions=[
                    Action(
                        timestamp="09:55",
                        purpose="Check status",
                        method="kubectl get pods",
                        findings="Crashloop detected",
                    )
                ],
            )
        ],
    )


def _make_roles() -> RoleAnalysis:
    return RoleAnalysis(
        incident_id="#incident-test",
        channel="#incident-test",
        participants=[
            ParticipantRole(
                user_name="alice",
                inferred_role="Incident Commander",
                confidence="high",
                evidence=["assigned tasks to team"],
            )
        ],
        relationships=[
            Relationship(
                from_user="bob",
                to_user="alice",
                relationship_type="reports_to",
                description="Bob updated Alice",
            )
        ],
    )


def _make_tactics() -> list[Tactic]:
    return [
        Tactic(
            id="tac-20260319-001",
            title="Check pod status",
            purpose="Identify crashlooping pods",
            category="container-analysis",
            tools=["kubectl"],
            procedure="Run kubectl get pods -n <namespace>",
            observations="Pods in CrashLoopBackOff need log inspection",
            tags=["kubernetes"],
            confidence="confirmed",
            evidence="Alice shared kubectl output in channel",
            source=TacticSource(channel="#incident-test", participants=["alice"]),
            created_at="2026-03-19",
        )
    ]


# ---------------------------------------------------------------------------
# make_incident_id
# ---------------------------------------------------------------------------

def test_make_incident_id_is_deterministic():
    export = _make_export()
    id1 = make_incident_id(export)
    id2 = make_incident_id(export)
    assert id1 == id2


def test_make_incident_id_length():
    assert len(make_incident_id(_make_export())) == 12


def test_make_incident_id_differs_for_different_exports():
    e1 = _make_export()
    e2 = ProcessedExport(
        export_timestamp="2026-03-20T10:00:00Z",
        channel_name="#other-channel",
        messages=[],
    )
    assert make_incident_id(e1) != make_incident_id(e2)


# ---------------------------------------------------------------------------
# generate_markdown_report
# ---------------------------------------------------------------------------

def test_markdown_report_contains_title():
    md = generate_markdown_report(
        _make_export(), _make_summary(), _make_activity(), _make_roles(), _make_tactics()
    )
    assert "API Server Outage" in md


def test_markdown_report_contains_severity():
    md = generate_markdown_report(
        _make_export(), _make_summary(), _make_activity(), _make_roles(), []
    )
    assert "high" in md


def test_markdown_report_contains_participant():
    md = generate_markdown_report(
        _make_export(), _make_summary(), _make_activity(), _make_roles(), []
    )
    assert "@alice" in md


def test_markdown_report_contains_role():
    md = generate_markdown_report(
        _make_export(), _make_summary(), _make_activity(), _make_roles(), []
    )
    assert "Incident Commander" in md


def test_markdown_report_contains_tactic():
    md = generate_markdown_report(
        _make_export(), _make_summary(), _make_activity(), _make_roles(), _make_tactics()
    )
    assert "tac-20260319-001" in md
    assert "Check pod status" in md


def test_markdown_report_no_tactic_section_when_empty():
    md = generate_markdown_report(
        _make_export(), _make_summary(), _make_activity(), _make_roles(), []
    )
    assert "Extracted Investigation Tactics" not in md


def test_markdown_report_contains_timeline():
    md = generate_markdown_report(
        _make_export(), _make_summary(), _make_activity(), _make_roles(), []
    )
    assert "alert triggered" in md


# ---------------------------------------------------------------------------
# generate_json_report
# ---------------------------------------------------------------------------

def test_json_report_has_required_keys():
    report = generate_json_report(
        _make_export(), _make_summary(), _make_activity(), _make_roles(), _make_tactics()
    )
    for key in ("incident_id", "lang", "metadata", "summary", "activity", "roles", "tactics"):
        assert key in report


def test_json_report_default_lang_is_en():
    report = generate_json_report(
        _make_export(), _make_summary(), _make_activity(), _make_roles(), []
    )
    assert report["lang"] == "en"


def test_json_report_custom_lang():
    report = generate_json_report(
        _make_export(), _make_summary(), _make_activity(), _make_roles(), [], lang="ja"
    )
    assert report["lang"] == "ja"


def test_json_report_metadata_channel():
    report = generate_json_report(
        _make_export(), _make_summary(), _make_activity(), _make_roles(), []
    )
    assert report["metadata"]["channel"] == "#incident-test"


def test_json_report_tactics_list():
    report = generate_json_report(
        _make_export(), _make_summary(), _make_activity(), _make_roles(), _make_tactics()
    )
    assert len(report["tactics"]) == 1
    assert report["tactics"][0]["id"] == "tac-20260319-001"


def test_json_report_incident_id_matches_make_incident_id():
    export = _make_export()
    report = generate_json_report(
        export, _make_summary(), _make_activity(), _make_roles(), []
    )
    assert report["incident_id"] == make_incident_id(export)
