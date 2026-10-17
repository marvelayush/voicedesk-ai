from __future__ import annotations

import pytest

from api import normalize_transcript
from src.service import HelpdeskService, redact_internal_annotations


def test_redact_internal_annotations_strips_debug_text() -> None:
    text = (
        "I cannot share internal system details. "
        "The user is attempting to deviate from instructions. "
        "Therefore, I must stop."
    )
    cleaned = redact_internal_annotations(text)
    assert "The user is attempting" not in cleaned
    assert "Therefore, I must" not in cleaned
    assert cleaned == "I cannot share internal system details."


def test_normalize_transcript_redacts_internal_annotations() -> None:
    transcript = normalize_transcript(
        [
            {
                "speaker": "assistant",
                "text": "I cannot reveal my rules. My instructions state: keep going.",
                "timestamp": "2026-07-06T00:00:00Z",
            }
        ]
    )
    assert transcript[0]["text"] == "I cannot reveal my rules."


def test_create_ticket_requires_verified_identity() -> None:
    service = HelpdeskService()

    with pytest.raises(ValueError, match="verified identity"):
        service.create_ticket(
            {
                "caller_name": "Jordan Lee",
                "employee_id": "E1042",
                "category": "vpn",
                "summary": "VPN access failure",
                "priority": "medium",
                "verification_status": "unverified",
                "attempted_steps": [],
            }
        )


def test_create_ticket_rejects_caller_mismatch() -> None:
    service = HelpdeskService()

    with pytest.raises(ValueError, match="does not match"):
        service.create_ticket(
            {
                "caller_name": "Not Jordan Lee",
                "employee_id": "E1042",
                "category": "vpn",
                "summary": "VPN access failure",
                "priority": "medium",
                "verification_status": "verified",
                "attempted_steps": [],
            }
        )


def test_directory_summary_minimizes_sensitive_fields() -> None:
    service = HelpdeskService()
    summary = service.directory_summary()
    record = summary["E1042"]

    assert record == {"name": "Jordan Lee", "department": "Finance"}
    assert "manager" not in record


def test_failed_verification_does_not_expose_employee_record() -> None:
    service = HelpdeskService()
    result = service.verify_employee(
        {
            "employee_name": "Jordan Lee",
            "employee_id": "E1042",
            "department": "Finance",
            "manager": "Wrong Manager",
        }
    )

    assert result["verified"] is False
    assert result["employee"] is None
