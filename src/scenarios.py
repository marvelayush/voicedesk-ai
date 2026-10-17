from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    summary: str
    category: str
    expected_outcome: str
    demo_path: str
    employee_name: str
    employee_id: str
    department: str
    manager: str
    issue_description: str
    runbook_key: str
    resolveable: bool
    follow_up_required: bool


SCENARIOS = [
    Scenario(
        id="vpn_issue",
        title="VPN access failure after password reset",
        summary="A verified employee cannot connect to the VPN after resetting a password. The demo should escalate after runbook steps fail.",
        category="vpn",
        expected_outcome="Escalate to network support",
        demo_path="Verify -> troubleshoot -> escalate",
        employee_name="Jordan Lee",
        employee_id="E1042",
        department="Finance",
        manager="Priya Patel",
        issue_description="I can sign in, but the VPN keeps failing with an authentication error.",
        runbook_key="vpn",
        resolveable=False,
        follow_up_required=True,
    ),
    Scenario(
        id="mfa_issue",
        title="MFA re-enrollment",
        summary="The caller lost access to their MFA device and needs a safe guided recovery flow.",
        category="mfa",
        expected_outcome="Resolved during call",
        demo_path="Verify -> resolve",
        employee_name="Mia Chen",
        employee_id="E1188",
        department="Marketing",
        manager="Dana Brooks",
        issue_description="My authenticator app got wiped and I cannot approve sign-ins.",
        runbook_key="mfa",
        resolveable=True,
        follow_up_required=False,
    ),
    Scenario(
        id="password_reset",
        title="Locked account / password reset",
        summary="A straightforward account lockout should resolve quickly and show the happy-path demo.",
        category="password_reset",
        expected_outcome="Resolved during call",
        demo_path="Verify -> resolve",
        employee_name="Sam Rivera",
        employee_id="E2031",
        department="Operations",
        manager="Nina Gomez",
        issue_description="I locked myself out after too many attempts and need access back.",
        runbook_key="password_reset",
        resolveable=True,
        follow_up_required=False,
    ),
    Scenario(
        id="outlook_outage",
        title="Outlook sync issue during active incident",
        summary="The triage agent should detect the incident feed and avoid wasting time on runbooks.",
        category="email",
        expected_outcome="Escalate due known incident",
        demo_path="Verify -> triage -> escalate",
        employee_name="Taylor Kim",
        employee_id="E7721",
        department="Sales",
        manager="Leah Ford",
        issue_description="Outlook stopped syncing and I see errors on every device.",
        runbook_key="email",
        resolveable=False,
        follow_up_required=True,
    ),
]

