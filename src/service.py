from __future__ import annotations

import itertools
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.nebius_client import NebiusClient
from src.scenarios import Scenario, SCENARIOS


RUNBOOK_DIR = Path(__file__).resolve().parent.parent / "runbooks"

# Keyword hints used when no LLM is configured. Order matters: the first match wins.
_CATEGORY_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("vpn", ("vpn", "remote access", "tunnel")),
    ("mfa", ("mfa", "authenticator", "2fa", "two-factor", "approve sign-ins", "one-time code")),
    ("password_reset", ("password", "locked out", "locked myself", "lockout", "account locked")),
    ("email", ("outlook", "email", "mailbox", "inbox", "syncing")),
    ("billing", ("billing", "invoice", "expense")),
)


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


def classify_issue(text: str) -> str:
    """Deterministic keyword classifier used as the fallback for LLM routing."""
    blob = str(text).lower()
    for category, keywords in _CATEGORY_KEYWORDS:
        if any(keyword in blob for keyword in keywords):
            return category
    return "unknown"


def load_runbooks(directory: Path = RUNBOOK_DIR) -> dict[str, list[str]]:
    """Read numbered steps from runbooks/*.md so the KB and the demo share one source."""
    runbooks: dict[str, list[str]] = {}
    if not directory.is_dir():
        return runbooks
    for path in sorted(directory.glob("*.md")):
        steps = [
            match.group(1).strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if (match := re.match(r"^\s*\d+\.\s+(.+)$", line))
        ]
        if steps:
            runbooks[path.stem] = steps
    return runbooks


def transcript_to_text(transcript: list[dict[str, Any]]) -> str:
    return "\n".join(f"{turn.get('speaker', 'unknown')}: {turn.get('text', '')}" for turn in transcript)


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
    route_source: str = ""
    incident_active: bool = False
    resolved: bool = False
    escalated: bool = False
    identity_hold: bool = False
    ticket_id: str = ""
    follow_up_required: bool = False
    attempted_steps: list[str] = field(default_factory=list)
    escalation_draft: str = ""
    escalation_source: str = ""
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
        self.runbooks = load_runbooks()
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

    def list_tickets(self, status: str | None = None) -> list[dict[str, Any]]:
        if not status:
            return list(self.tickets)
        return [ticket for ticket in self.tickets if ticket.get("status") == status]

    def runbook_steps(self, key: str) -> list[str]:
        return self.runbooks.get(key, [])

    def build_review(self, call_id: str, transcript: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
        return CallOrchestrator.build_review_record(call_id=call_id, transcript=transcript, state=state)


class CallOrchestrator:
    def __init__(self, service: HelpdeskService, nebius: NebiusClient | None = None) -> None:
        self.service = service
        self.nebius = nebius if nebius is not None else NebiusClient()
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
            review = self.build_review_record(
                call_id=state.call_id,
                transcript=state.transcript,
                state=asdict(state),
            )
            review["summary_source"] = "rules"
            if self.nebius.enabled:
                summary = self.nebius.summarize_transcript(
                    transcript_to_text(state.transcript), fallback=review["summary"]
                )
                if summary and summary != review["summary"]:
                    review["summary"] = summary
                    review["summary_source"] = "nebius"
            state.review = review
        return state

    @staticmethod
    def build_review_record(call_id: str, transcript: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
        resolved = bool(state.get("resolved"))
        verified = bool(state.get("verified"))
        escalated = bool(state.get("escalated"))
        identity_hold = bool(state.get("identity_hold"))
        follow_up_required = bool(state.get("follow_up_required"))
        issue_category = state.get("issue_category", "unknown")
        ticket_id = state.get("ticket_id", "")
        # An unverified caller is handled correctly when nothing account-changing happened.
        correct_process = (verified and (resolved or escalated)) or (
            not verified and not resolved and not ticket_id
        )
        notes = []
        if not verified:
            notes.append("Verification was incomplete.")
        if identity_hold:
            notes.append("Identity hold applied: no account changes or tickets were made for an unverified caller.")
        if not verified and ticket_id:
            notes.append("A ticket was created without verified identity.")
        if escalated and not resolved:
            notes.append("Escalation was appropriate for the unresolved issue.")
        if resolved:
            notes.append("Caller was resolved during the session.")
        if follow_up_required:
            notes.append("Follow-up is required.")
        if resolved:
            summary = "Caller issue was resolved."
        elif identity_hold:
            summary = "Caller could not be verified, so the request was held for identity confirmation."
        else:
            summary = "Caller issue was not resolved and required escalation."
        agents_involved: list[str] = []
        for turn in transcript:
            speaker = str(turn.get("speaker", ""))
            if speaker.endswith("_agent") and speaker not in agents_involved:
                agents_involved.append(speaker)
        return {
            "call_id": call_id,
            "issue_category": issue_category,
            "employee_verified": verified,
            "resolved": resolved,
            "escalated": escalated,
            "identity_hold": identity_hold,
            "correct_process_followed": correct_process,
            "follow_up_required": follow_up_required,
            "attempted_steps": state.get("attempted_steps", []),
            "ticket_id": ticket_id,
            "route_suggestion": state.get("route_suggestion", ""),
            "handoff_count": len(state.get("handoffs") or []),
            "agents_involved": agents_involved,
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
        self._suggest_route(state)
        if not state.verified:
            self._append(
                state,
                "triage_agent",
                "I can't make account changes until your identity is confirmed, so I'm placing this on an identity hold.",
            )
            state.identity_hold = True
            state.follow_up_required = True
            self._handoff(state, "triage", "escalation", "Caller unverified; identity hold before any account action.")
            return
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

    def _suggest_route(self, state: CallState) -> None:
        caller_text = " ".join(turn["text"] for turn in state.transcript if turn["speaker"] == "caller")
        fallback = classify_issue(caller_text)
        state.route_suggestion = fallback
        state.route_source = "rules"
        if self.nebius.enabled:
            suggestion = self.nebius.suggest_route(transcript_to_text(state.transcript), fallback=fallback)
            if suggestion:
                state.route_suggestion = suggestion
                state.route_source = "nebius"

    def _draft_escalation(self, state: CallState, scenario: Scenario, priority: str) -> None:
        steps = "; ".join(state.attempted_steps) or "none"
        incident = "active incident" if state.incident_active else "no active incident"
        fallback = (
            f"[{priority.upper()}] {scenario.category} issue for {scenario.employee_name} ({scenario.employee_id}). "
            f"Reported: {scenario.issue_description} Steps tried: {steps}. Incident feed: {incident}."
        )
        state.escalation_draft = fallback
        state.escalation_source = "rules"
        if self.nebius.enabled:
            draft = self.nebius.draft_escalation(transcript_to_text(state.transcript), asdict(state), fallback=fallback)
            if draft and draft != fallback:
                state.escalation_draft = draft
                state.escalation_source = "nebius"

    def _step_escalation(self, state: CallState) -> None:
        scenario = scenario_by_id(state.scenario_id)
        if state.identity_hold or not state.verified:
            # Never open a ticket against an employee record we could not verify.
            state.identity_hold = True
            state.follow_up_required = True
            state.escalation_draft = (
                f"Identity hold: caller claiming to be {scenario.employee_name} failed verification. "
                "Call back through a verified channel before taking any action."
            )
            state.escalation_source = "rules"
            self._append(
                state,
                "escalation_agent",
                "I've flagged this for the service desk. They'll contact you through a verified channel to confirm your identity first.",
            )
            state.phase = "review"
            state.active_agent = "review"
            self._append(state, "system", "Identity hold recorded. I'm moving to the post-call review.")
            return

        priority = "high" if state.incident_active else "medium"
        self._draft_escalation(state, scenario, priority)
        ticket = self.service.create_ticket(
            {
                "caller_name": scenario.employee_name,
                "employee_id": scenario.employee_id,
                "category": scenario.category,
                "summary": scenario.issue_description,
                "priority": priority,
                "verification_status": "verified",
                "attempted_steps": state.attempted_steps,
                "escalation_notes": state.escalation_draft,
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
