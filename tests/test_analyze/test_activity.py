"""Tests for analyze.activity module."""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock

from aiir.analyze.activity import (
    _build_system_prompt,
    analyze_activity,
    format_activity_markdown,
)
from aiir.models import ActivityAnalysis, ParticipantActivity, Action, ProcessedExport, ProcessedMessage


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
        text=f"<user_message_{nonce}>ran kubectl get pods</user_message_{nonce}>",
    )
    bot_msg = ProcessedMessage(
        user_id="B001",
        user_name="alertbot",
        post_type="bot",
        timestamp="2026-03-19T09:54:00Z",
        timestamp_unix="1742378040.000000",
        text="Alert fired!",
    )
    return ProcessedExport(
        export_timestamp="2026-03-19T10:00:00Z",
        channel_name="#incident-test",
        messages=[msg, bot_msg],
        sanitization_nonce=nonce,
    )


SAMPLE_ANALYSIS_JSON = json.dumps({
    "incident_id": "#incident-test",
    "channel": "#incident-test",
    "participants": [
        {
            "user_name": "alice",
            "role_hint": "Lead Responder",
            "actions": [
                {
                    "timestamp": "2026-03-19 09:55:00",
                    "purpose": "Check pod status",
                    "method": "kubectl get pods",
                    "findings": "Found crashlooping pods",
                }
            ],
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


def test_system_prompt_requires_json_schema():
    prompt = _build_system_prompt("x")
    assert "participants" in prompt
    assert "actions" in prompt


def test_system_prompt_instructs_preserve_defanged_iocs():
    prompt = _build_system_prompt("x")
    assert "hxxp" in prompt
    assert "refang" in prompt


# ---------------------------------------------------------------------------
# analyze_activity
# ---------------------------------------------------------------------------

def test_analyze_activity_returns_model():
    export = _make_export()
    client = _make_client(SAMPLE_ANALYSIS_JSON)
    result = analyze_activity(export, client)
    assert isinstance(result, ActivityAnalysis)
    assert result.channel == "#incident-test"
    assert len(result.participants) == 1
    assert result.participants[0].user_name == "alice"


def test_analyze_activity_invalid_json_raises():
    export = _make_export()
    client = _make_client("not valid json {{{")
    with pytest.raises(ValueError, match="invalid JSON"):
        analyze_activity(export, client)


def test_analyze_activity_uses_export_nonce():
    """The nonce from the export should appear in the system prompt sent to the LLM."""
    export = _make_export(nonce="mynonce99")
    client = _make_client(SAMPLE_ANALYSIS_JSON)
    analyze_activity(export, client)
    call_args = client.complete_json.call_args
    system_prompt = call_args[0][0]
    assert "mynonce99" in system_prompt


def test_analyze_activity_fallback_nonce_when_missing():
    """A fallback nonce is generated when export.sanitization_nonce is empty."""
    export = _make_export(nonce="")
    export.sanitization_nonce = ""
    client = _make_client(SAMPLE_ANALYSIS_JSON)
    analyze_activity(export, client)
    call_args = client.complete_json.call_args
    system_prompt = call_args[0][0]
    # Should still contain a nonce tag even without one set
    assert "<user_message_" in system_prompt


# ---------------------------------------------------------------------------
# format_activity_markdown
# ---------------------------------------------------------------------------

def _make_analysis() -> ActivityAnalysis:
    return ActivityAnalysis(
        incident_id="#incident-test",
        channel="#incident-test",
        participants=[
            ParticipantActivity(
                user_name="alice",
                role_hint="Lead Responder",
                actions=[
                    Action(
                        timestamp="2026-03-19 09:55:00",
                        purpose="Check pod status",
                        method="kubectl get pods",
                        findings="Found crashlooping pods",
                    )
                ],
            )
        ],
    )


def test_format_markdown_contains_username():
    md = format_activity_markdown(_make_analysis())
    assert "@alice" in md


def test_format_markdown_contains_role():
    md = format_activity_markdown(_make_analysis())
    assert "Lead Responder" in md


def test_format_markdown_contains_table_header():
    md = format_activity_markdown(_make_analysis())
    assert "| Time | Purpose | Method | Findings |" in md


def test_format_markdown_escapes_pipe_in_findings():
    analysis = ActivityAnalysis(
        incident_id="x",
        channel="x",
        participants=[
            ParticipantActivity(
                user_name="bob",
                role_hint="SME",
                actions=[
                    Action(
                        timestamp="T",
                        purpose="test",
                        method="cmd | grep",
                        findings="a | b",
                    )
                ],
            )
        ],
    )
    md = format_activity_markdown(analysis)
    assert r"\|" in md
