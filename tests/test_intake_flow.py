from src.scenarios import SCENARIOS
from src.service import CallOrchestrator, HelpdeskService


def test_intake_waits_for_issue_before_handoff() -> None:
    service = HelpdeskService()
    orchestrator = CallOrchestrator(service)
    scenario = SCENARIOS[0]

    state = orchestrator.start_call(scenario)

    assert state.phase == "intake_waiting"
    assert state.active_agent == "intake"
    assert state.handoffs == []
    assert state.transcript[-1]["speaker"] == "intake_agent"
    assert "What issue are you experiencing today?" in state.transcript[-1]["text"]

    state = orchestrator.advance(state)

    assert state.phase == "verification"
    assert state.active_agent == "verification"
    assert state.transcript[-2]["speaker"] == "caller"
    assert state.transcript[-1]["speaker"] == "intake_agent"
    assert state.handoffs[0]["from"] == "intake"
    assert state.handoffs[0]["to"] == "verification"
