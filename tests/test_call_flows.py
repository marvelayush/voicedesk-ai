from __future__ import annotations

import pytest

from src.scenarios import SCENARIOS
from src.service import (
    CallOrchestrator,
    HelpdeskService,
    classify_issue,
    load_runbooks,
    scenario_by_id,
)


def run_to_review(scenario_id: str) -> tuple[HelpdeskService, object]:
    service = HelpdeskService()
    orchestrator = CallOrchestrator(service)
    state = orchestrator.start_call(scenario_by_id(scenario_id))
    for _ in range(10):
        if state.phase == "review":
            break
        state = orchestrator.advance(state)
    state = orchestrator.sync_review_if_needed(state)
    return service, state


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
def test_every_scenario_reaches_review_with_correct_process(scenario) -> None:
    _, state = run_to_review(scenario.id)

    assert state.phase == "review"
    assert state.review["correct_process_followed"] is True
    assert state.route_suggestion == scenario.category
    assert state.route_source == "rules"
    assert state.review["summary_source"] == "rules"


def test_resolvable_scenario_does_not_create_ticket() -> None:
    service, state = run_to_review("mfa_issue")

    assert state.resolved is True
    assert state.ticket_id == ""
    assert service.tickets == []


def test_known_incident_skips_runbook_and_creates_high_priority_ticket() -> None:
    service, state = run_to_review("outlook_outage")

    assert state.incident_active is True
    assert state.attempted_steps == []
    assert service.tickets[0]["priority"] == "high"
    assert service.tickets[0]["escalation_notes"] == state.escalation_draft
    assert "resolution" not in [h["to"] for h in state.handoffs]


def test_failed_runbook_escalates_with_attempted_steps() -> None:
    service, state = run_to_review("vpn_issue")

    assert state.escalated is True
    assert state.ticket_id == service.tickets[0]["ticket_id"]
    assert service.tickets[0]["attempted_steps"] == state.attempted_steps
    assert state.attempted_steps, "runbook steps should be recorded"
    assert state.escalation_draft.startswith("[MEDIUM] vpn issue")


def test_unverified_caller_gets_identity_hold_and_no_ticket() -> None:
    service, state = run_to_review("unverified_caller")

    assert state.verified is False
    assert state.identity_hold is True
    assert state.resolved is False
    assert state.ticket_id == ""
    assert service.tickets == []
    assert state.attempted_steps == []
    assert state.review["identity_hold"] is True
    assert "identity" in state.review["summary"].lower()


def test_review_reports_agents_and_handoffs() -> None:
    _, state = run_to_review("vpn_issue")

    assert state.review["handoff_count"] == len(state.handoffs)
    assert state.review["agents_involved"][0] == "intake_agent"
    assert "escalation_agent" in state.review["agents_involved"]


def test_runbooks_load_from_markdown_files() -> None:
    runbooks = load_runbooks()

    assert set(runbooks) >= {"vpn", "mfa", "password_reset", "email"}
    assert all(steps for steps in runbooks.values())
    assert not any(step[0].isdigit() for steps in runbooks.values() for step in steps)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("The VPN keeps failing", "vpn"),
        ("My authenticator app got wiped", "mfa"),
        ("I locked myself out", "password_reset"),
        ("Outlook stopped syncing", "email"),
        ("My monitor is flickering", "unknown"),
    ],
)
def test_classify_issue(text: str, expected: str) -> None:
    assert classify_issue(text) == expected
