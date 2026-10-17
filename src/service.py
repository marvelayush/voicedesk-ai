from __future__ import annotations

import itertools
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.scenarios import Scenario, SCENARIOS


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def scenario_by_id(scenario_id: str) -> Scenario:
    for scenario in SCENARIOS:
        if scenario.id == scenario_id:
            return scenario
    raise KeyError(f"Unknown scenario: {scenario_id}")


_INTERNAL_ANNOTATION_MARKERS = (
    "The user is attempting",
    "My instructions state:",
    "Therefore, I must",
    "I need to re-engage the user.",
)


def redact_internal_annotations(text: str) -> str:
    cleaned = str(text)
    for marker in _INTERNAL_ANNOTATION_MARKERS:
        if marker in cleaned:
            cleaned = cleaned.split(marker, 1)[0].rstrip()
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned


@dataclass
class CallState:
    call_id: str
    scenario_id: str
    active_agent: str = "intake"
    phase: str = "intake"
    transcript: list[dict[str, str]] = field(default_factory=list)
    handoffs: list[dict[str, str]] = field(default_factory=list)
    verified: bool = False
    verification_notes: str = ""
    issue_category: str = ""
    route_suggestion: str = ""
    incident_active: bool = False
    resolved: bool = False
    escalated: bool = False
    ticket_id: str = ""
    follow_up_required: bool = False
    attempted_steps: list[str] = field(default_factory=list)
    escalation_draft: str = ""
    review: dict[str, Any] = field(default_factory=dict)
    finished: bool = False


class HelpdeskService:
    def __init__(self) -> None:
        self.directory = {
            "E1042": {"name": "Jordan Lee", "department": "Finance", "manager": "Priya Patel", "status": "active"},
            "E1188": {"name": "Mia Chen", "department": "Marketing", "manager": "Dana Brooks", "status": "active"},
            "E2031": {"name": "Sam Rivera", "department": "Operations", "manager": "Nina Gomez", "status": "active"},
            "E7721": {"name": "Taylor Kim", "department": "Sales", "manager": "Leah Ford", "status": "active"},
        }
        self.incidents = {
            "vpn": {"active": False, "summary": "No active VPN outage."},
            "mfa": {"active": False, "summary": "No active MFA incident."},
            "password_reset": {"active": False, "summary": "No active password reset incident."},
            "email": {"active": True, "summary": "Known Outlook sync outage affecting a subset of users."},
        }
        self.runbooks = {
            "vpn": [
                "Confirm the user's VPN client is up to date.",
                "Confirm the user is on the approved network profile.",
                "Have the user disconnect and reconnect once.",
                "If authentication still fails, escalate to network support.",
            ],
            "mfa": [
                "Confirm the caller still has access to the recovery phone or email.",
                "Walk through MFA device re-enrollment.",
                "Have the user re-test sign-in once enrolled.",
            ],
            "password_reset": [
                "Confirm the account is active.",
                "Use the password reset recovery flow.",
                "Ask the user to sign out and sign back in.",
            ],
            "email": [
                "Confirm whether other users are affected.",
                "Check for a known incident before troubleshooting locally.",
                "If the outage is active, escalate to the collaboration team.",
            ],
        }
        self._ticket_counter = itertools.count(1042)
        self.tickets: list[dict[str, Any]] = []

    def verify_employee(self, payload: dict[str, Any]) -> dict[str, Any]:
        employee_id = str(payload.get("employee_id") or "").strip()
        employee_name = str(payload.get("employee_name") or "").strip().lower()
        record = self.directory.get(employee_id) if employee_id else None
        if record is None and employee_name:
            for candidate_id, candidate in self.directory.items():
                if candidate["name"].lower() == employee_name:
                    record = candidate
                    employee_id = candidate_id
                    break
        verified = bool(
            record
            and (not employee_name or record["name"].lower() == employee_name)
            and (payload.get("department") in (None, "", record["department"]))
            and (payload.get("manager") in (None, "", record["manager"]))
        )
        return {
            "verified": verified,
            "record_found": bool(record),
            "employee": record if verified else None,
            "timestamp": now_iso(),
        }

    def get_incident_status(self, category: str) -> dict[str, Any]:
        incident = self.incidents.get(category, {"active": False, "summary": "No incident record found."})
        return {"category": category, **incident, "timestamp": now_iso()}

    def create_ticket(self, payload: dict[str, Any]) -> dict[str, Any]:
        caller_name = str(payload.get("caller_name") or "").strip()
        employee_id = str(payload.get("employee_id") or "").strip()
        verification_status = str(payload.get("verification_status") or "").strip().lower()
        employee_record = self.directory.get(employee_id) if employee_id else None
        if verification_status != "verified":
            raise ValueError("ticket creation requires verified identity")
        if not employee_record:
            raise ValueError("ticket creation requires a known employee_id")
        if caller_name.lower() != employee_record["name"].lower():
            raise ValueError("ticket caller name does not match verified employee_id")
        ticket_id = f"HD-{next(self._ticket_counter)}"
        ticket = {
            "ticket_id": ticket_id,
            "created_at": now_iso(),
            "status": "open",
            **payload,
        }
        self.tickets.append(ticket)
        return ticket

    def directory_summary(self) -> dict[str, Any]:
        return {
            employee_id: {
                "name": record["name"],
                "department": record["department"],
            }
            for employee_id, record in self.directory.items()
        }

    def incident_summary(self) -> dict[str, Any]:
        return self.incidents

    def ticket_summary(self) -> list[dict[str, Any]]:
        return self.tickets[-5:]

    def runbook_steps(self, key: str) -> list[str]:
        return self.runbooks.get(key, [])

    def build_review(self, call_id: str, transcript: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
        return CallOrchestrator.build_review_record(call_id=call_id, transcript=transcript, state=state)


class CallOrchestrator:
    def __init__(self, service: HelpdeskService) -> None:
        self.service = service
        self._call_counter = itertools.count(1)

    def start_call(self, scenario: Scenario) -> CallState:
        state = CallState(call_id=f"call_{next(self._call_counter):03d}", scenario_id=scenario.id)
        self._append(state, "system", f"Call started for scenario '{scenario.title}'.")
        self._step_intake_greeting(state)
        return state

    def advance(self, state: CallState) -> CallState:
        if state.finished:
            return state
        if state.phase == "intake_waiting":
            self._step_intake_capture(state)
        elif state.phase == "verification":
            self._step_verification(state)
        elif state.phase == "triage":
            self._step_triage(state)
        elif state.phase == "resolution":
            self._step_resolution(state)
        elif state.phase == "escalation":
            self._step_escalation(state)
        elif state.phase == "review":
            state.finished = True
        return state

    def sync_review_if_needed(self, state: CallState) -> CallState:
        if state.phase == "review" and not state.review:
            state.review = self.build_review_record(
                call_id=state.call_id,
                transcript=state.transcript,
                state=asdict(state),
            )
        return state

    @staticmethod
    def build_review_record(call_id: str, transcript: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
        resolved = bool(state.get("resolved"))
        verified = bool(state.get("verified"))
        escalated = bool(state.get("escalated"))
        follow_up_required = bool(state.get("follow_up_required"))
        issue_category = state.get("issue_category", "unknown")
        correct_process = verified and (resolved or escalated)
        notes = []
        if not verified:
            notes.append("Verification was incomplete.")
        if escalated and not resolved:
            notes.append("Escalation was appropriate for the unresolved issue.")
        if resolved:
            notes.append("Caller was resolved during the session.")
        if follow_up_required:
            notes.append("Follow-up is required.")
        summary = (
            "Caller issue was resolved." if resolved else "Caller issue was not resolved and required escalation."
        )
        return {
            "call_id": call_id,
            "issue_category": issue_category,
            "employee_verified": verified,
            "resolved": resolved,
            "escalated": escalated,
            "correct_process_followed": correct_process,
            "follow_up_required": follow_up_required,
            "attempted_steps": state.get("attempted_steps", []),
            "ticket_id": state.get("ticket_id", ""),
            "qa_notes": notes,
            "summary": summary,
            "transcript_turns": len(transcript),
            "generated_at": now_iso(),
        }

    def _append(self, state: CallState, speaker: str, text: str) -> None:
        state.transcript.append(
            {
                "speaker": speaker,
                "text": redact_internal_annotations(text),
                "timestamp": now_iso(),
            }
        )

    def _handoff(self, state: CallState, from_agent: str, to_agent: str, reason: str) -> None:
        state.handoffs.append(
            {
                "timestamp": now_iso(),
                "from": from_agent,
                "to": to_agent,
                "reason": reason,
            }
        )
        state.active_agent = to_agent
        state.phase = to_agent

    def _step_intake_greeting(self, state: CallState) -> None:
        self._append(
            state,
            "intake_agent",
            "Thanks for calling IT support. What issue are you experiencing today?",
        )
        state.phase = "intake_waiting"
        state.active_agent = "intake"

    def _step_intake_capture(self, state: CallState) -> None:
        scenario = scenario_by_id(state.scenario_id)
        self._append(state, "caller", scenario.issue_description)
        self._append(
            state,
            "intake_agent",
            f"I heard: '{scenario.issue_description}'. I'll verify your details and route this the right way.",
        )
        self._handoff(state, "intake", "verification", "Intake captured issue details and moved to verification.")

    def _step_verification(self, state: CallState) -> None:
        scenario = scenario_by_id(state.scenario_id)
        result = self.service.verify_employee(
            {
                "employee_name": scenario.employee_name,
                "employee_id": scenario.employee_id,
                "department": scenario.department,
                "manager": scenario.manager,
            }
        )
        state.verified = bool(result["verified"])
        state.verification_notes = (
            f"Verified {scenario.employee_name} in {scenario.department}." if state.verified else "Verification failed."
        )
        self._append(
            state,
            "verification_agent",
            "Thanks, I’ve confirmed your details. I’m moving to the next step now."
            if state.verified
            else "I couldn't fully verify your details, so I'll use a restricted support path.",
        )
        self._handoff(state, "verification", "triage", "Verification finished.")

    def _step_triage(self, state: CallState) -> None:
        scenario = scenario_by_id(state.scenario_id)
        state.issue_category = scenario.category
        incident = self.service.get_incident_status(scenario.category)
        state.incident_active = bool(incident["active"])
        if state.incident_active:
            self._append(
                state,
                "triage_agent",
                f"There is an active incident in {scenario.category}: {incident['summary']} I'm routing straight to escalation.",
            )
            state.follow_up_required = True
            self._handoff(state, "triage", "escalation", "Active incident detected.")
            return

        self._append(
            state,
            "triage_agent",
            "This looks like an individual issue, not a known incident. I’ll try the runbook first.",
        )
        self._handoff(state, "triage", "resolution", "No active incident; attempting runbook resolution.")

    def _step_resolution(self, state: CallState) -> None:
        scenario = scenario_by_id(state.scenario_id)
        steps = self.service.runbook_steps(scenario.runbook_key)
        state.attempted_steps.extend(steps[:3])
        if scenario.resolveable:
            state.resolved = True
            self._append(
                state,
                "resolution_agent",
                "We’ve completed the guided steps and the issue looks resolved. Please try signing in again.",
            )
            state.phase = "review"
            state.active_agent = "review"
            self._append(state, "system", "The issue is resolved. I’m moving to the post-call review.")
            return

        self._append(
            state,
            "resolution_agent",
            "I tried the runbook steps, but the issue is still there. I’m escalating with the steps we already tried.",
        )
        state.follow_up_required = True
        self._handoff(state, "resolution", "escalation", "Runbook did not resolve the issue.")

    def _step_escalation(self, state: CallState) -> None:
        scenario = scenario_by_id(state.scenario_id)
        ticket = self.service.create_ticket(
            {
                "caller_name": scenario.employee_name,
                "employee_id": scenario.employee_id,
                "category": scenario.category,
                "summary": scenario.issue_description,
                "priority": "high" if state.incident_active else "medium",
                "verification_status": "verified" if state.verified else "unverified",
                "attempted_steps": state.attempted_steps,
            }
        )
        state.ticket_id = ticket["ticket_id"]
        state.escalated = True
        state.follow_up_required = True
        self._append(
            state,
            "escalation_agent",
            f"I’ve created ticket {ticket['ticket_id']} and sent this to the right support queue.",
        )
        state.phase = "review"
        state.active_agent = "review"
        self._append(state, "system", "The issue has been escalated. I’m moving to the post-call review.")
