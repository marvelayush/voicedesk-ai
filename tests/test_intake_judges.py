from src.intake_judges import (
    build_clarification_judge_payload,
    build_issue_capture_judge_payload,
    parse_judge_result,
    serialize_trace_for_judge,
)


def test_parse_judge_result_accepts_valid_json() -> None:
    raw = {
        "score": 1.0,
        "label": "pass",
        "rationale": "The agent asked a timely clarifying question.",
    }
    result = parse_judge_result(raw)
    assert result["score"] == 1.0
    assert result["label"] == "pass"


def test_parse_judge_result_falls_back_on_malformed_payload() -> None:
    result = parse_judge_result({"unexpected": "value"})
    assert result["score"] == 0.0
    assert result["label"] in {"partial", "fail"}


def test_build_clarification_judge_payload_includes_full_trace() -> None:
    payload = build_clarification_judge_payload(
        case_id="H11",
        caller_input="I cannot access a shared folder that I used yesterday.",
        hidden_context="user recently accessed finance share",
        expected_next_action="route_to_verification",
        observed_next_action="ask_clarifying_question",
        conversation_text="Caller: ...\nAssistant: ...",
    )
    assert "conversation_text" in payload
    assert payload["case_id"] == "H11"


def test_build_issue_capture_judge_payload_includes_full_trace() -> None:
    payload = build_issue_capture_judge_payload(
        case_id="H11",
        caller_input="I cannot access a shared folder that I used yesterday.",
        hidden_context="user recently accessed finance share",
        expected_next_action="route_to_verification",
        observed_next_action="ask_clarifying_question",
        conversation_text="Caller: ...\nAssistant: ...",
    )
    assert "conversation_text" in payload
    assert payload["case_id"] == "H11"


def test_serialize_trace_for_judge_includes_nested_child_runs() -> None:
    class Run:
        def __init__(self, name: str, run_type: str, inputs=None, outputs=None, child_runs=None):
            self.name = name
            self.run_type = run_type
            self.inputs = inputs
            self.outputs = outputs
            self.child_runs = child_runs or []

    trace = Run(
        "root",
        "chain",
        inputs={"caller_input": "hello"},
        outputs={"observed_next_action": "stay_in_intake"},
        child_runs=[Run("llm", "llm", inputs={"prompt": "x"}, outputs={"text": "y"})],
    )
    serialized = serialize_trace_for_judge(trace)
    assert "root" in serialized
    assert "llm" in serialized
    assert "observed_next_action" in serialized
