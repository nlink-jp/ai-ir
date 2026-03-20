"""Tests for analyze.roles module."""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock

from aiir.analyze.roles import (
    _build_system_prompt,
    analyze_roles,
    format_roles_markdown,
)
from aiir.models import (
    ParticipantRole,
    Relationship,
    RoleAnalysis,
    ProcessedExport,
    ProcessedMessage,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_export(nonce: str = "testnonce") -> ProcessedExport:
    msg = ProcessedMessage(
        user_id="U001",
        user_name="alice",
        post_type="user",
        timestamp="2026-03-19T09:55:00Z",
        timestamp_unix="1742378100.000000",
        text=f"<user_message_{nonce}>assigning tasks to team</user_message_{nonce}>",
    )
    return ProcessedExport(
        export_timestamp="2026-03-19T10:00:00Z",
        channel_name="#incident-test",
        messages=[msg],
        sanitization_nonce=nonce,
    )


SAMPLE_ROLES_JSON = json.dumps({
    "incident_id": "#incident-test",
    "channel": "#incident-test",
    "participants": [
        {
            "user_name": "alice",
            "inferred_role": "Incident Commander",
            "confidence": "high",
            "evidence": ["alice assigned tasks to the team"],
        }
    ],
    "relationships": [
        {
            "from_user": "bob",
            "to_user": "alice",
            "relationship_type": "reports_to",
            "description": "Bob updated Alice on progress",
        }
    ],
})


def _make_client(response: str) -> MagicMock:
    client = MagicMock()
    client.complete_json.return_value = response
    return client


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

def test_system_prompt_contains_nonce_tag():
    prompt = _build_system_prompt("abc123")
    assert "<user_message_abc123>" in prompt


def test_system_prompt_instructs_english():
    prompt = _build_system_prompt("x")
    assert "English" in prompt


def test_system_prompt_lists_common_roles():
    prompt = _build_system_prompt("x")
    assert "Incident Commander" in prompt
    assert "Lead Responder" in prompt


def test_system_prompt_requires_json():
    prompt = _build_system_prompt("x")
    assert "participants" in prompt
    assert "relationships" in prompt


# ---------------------------------------------------------------------------
# analyze_roles
# ---------------------------------------------------------------------------

def test_analyze_roles_returns_model():
    export = _make_export()
    client = _make_client(SAMPLE_ROLES_JSON)
    result = analyze_roles(export, client)
    assert isinstance(result, RoleAnalysis)
    assert result.channel == "#incident-test"
    assert len(result.participants) == 1
    assert result.participants[0].user_name == "alice"
    assert result.participants[0].inferred_role == "Incident Commander"


def test_analyze_roles_includes_relationships():
    export = _make_export()
    client = _make_client(SAMPLE_ROLES_JSON)
    result = analyze_roles(export, client)
    assert len(result.relationships) == 1
    assert result.relationships[0].relationship_type == "reports_to"


def test_analyze_roles_invalid_json_raises():
    export = _make_export()
    client = _make_client("{broken json")
    with pytest.raises(ValueError, match="invalid JSON"):
        analyze_roles(export, client)


def test_analyze_roles_uses_export_nonce():
    export = _make_export(nonce="mynonce42")
    client = _make_client(SAMPLE_ROLES_JSON)
    analyze_roles(export, client)
    system_prompt = client.complete_json.call_args[0][0]
    assert "mynonce42" in system_prompt


def test_analyze_roles_fallback_nonce_when_missing():
    export = _make_export(nonce="")
    export.sanitization_nonce = ""
    client = _make_client(SAMPLE_ROLES_JSON)
    analyze_roles(export, client)
    system_prompt = client.complete_json.call_args[0][0]
    assert "<user_message_" in system_prompt


# ---------------------------------------------------------------------------
# format_roles_markdown
# ---------------------------------------------------------------------------

def _make_analysis() -> RoleAnalysis:
    return RoleAnalysis(
        incident_id="#incident-test",
        channel="#incident-test",
        participants=[
            ParticipantRole(
                user_name="alice",
                inferred_role="Incident Commander",
                confidence="high",
                evidence=["alice assigned tasks"],
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


def test_format_markdown_contains_username():
    md = format_roles_markdown(_make_analysis())
    assert "@alice" in md


def test_format_markdown_contains_role():
    md = format_roles_markdown(_make_analysis())
    assert "Incident Commander" in md


def test_format_markdown_contains_confidence_label():
    md = format_roles_markdown(_make_analysis())
    assert "HIGH" in md


def test_format_markdown_includes_evidence():
    md = format_roles_markdown(_make_analysis())
    assert "alice assigned tasks" in md


def test_format_markdown_includes_relationships_table():
    md = format_roles_markdown(_make_analysis())
    assert "reports_to" in md
    assert "| From | Relationship | To |" in md


def test_format_markdown_escapes_pipe_in_description():
    analysis = RoleAnalysis(
        incident_id="x",
        channel="x",
        participants=[],
        relationships=[
            Relationship(
                from_user="a",
                to_user="b",
                relationship_type="coordinates_with",
                description="left | right",
            )
        ],
    )
    md = format_roles_markdown(analysis)
    assert r"\|" in md
