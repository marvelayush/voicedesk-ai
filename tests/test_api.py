from __future__ import annotations

import pytest
from fastapi import HTTPException

import api


def test_list_scenarios_exposes_all_demo_scenarios() -> None:
    ids = {scenario["id"] for scenario in api.list_scenarios()}
    assert {"vpn_issue", "mfa_issue", "password_reset", "outlook_outage", "unverified_caller"} <= ids


def test_get_runbook_returns_steps_and_404s_for_unknown() -> None:
    assert api.get_runbook("vpn")["steps"]
    with pytest.raises(HTTPException) as exc:
        api.get_runbook("does_not_exist")
    assert exc.value.status_code == 404


def test_tickets_endpoint_lists_created_tickets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api, "service", api.HelpdeskService())
    api.create_ticket(
        api.TicketCreateRequest(
            caller_name="Jordan Lee",
            employee_id="E1042",
            category="vpn",
            summary="VPN failing",
            verification_status="verified",
        )
    )
    tickets = api.list_tickets()
    assert len(tickets) == 1
    assert api.list_tickets(status="open") == tickets
    assert api.list_tickets(status="closed") == []


def test_post_call_webhook_infers_category_from_transcript() -> None:
    review = api.elevenlabs_post_call(
        {
            "data": {
                "conversation_id": "conv_1",
                "transcript": [{"role": "user", "message": "My authenticator stopped working"}],
            }
        }
    )
    assert review["call_id"] == "conv_1"
    assert review["issue_category"] == "mfa"
