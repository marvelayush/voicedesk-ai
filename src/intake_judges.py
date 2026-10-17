from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


VALID_JUDGE_LABELS = {"pass", "partial", "fail"}


@dataclass(frozen=True)
class IntakeJudgeResult:
    score: float
    label: str
    rationale: str
    details: dict[str, Any] | None = None


def build_clarification_judge_payload(
    *,
    case_id: str,
    caller_input: str,
    hidden_context: str,
    expected_next_action: str,
    observed_next_action: str,
    conversation_text: str,
    expected_route: str | None = None,
    observed_route: str | None = None,
) -> dict[str, Any]:
    return _build_base_payload(
        case_id=case_id,
        judge_name="clarification_quality",
        caller_input=caller_input,
        hidden_context=hidden_context,
        expected_next_action=expected_next_action,
        observed_next_action=observed_next_action,
        conversation_text=conversation_text,
        expected_route=expected_route,
        observed_route=observed_route,
    )


def build_issue_capture_judge_payload(
    *,
    case_id: str,
    caller_input: str,
    hidden_context: str,
    expected_next_action: str,
    observed_next_action: str,
    conversation_text: str,
    expected_route: str | None = None,
    observed_route: str | None = None,
) -> dict[str, Any]:
    return _build_base_payload(
        case_id=case_id,
        judge_name="issue_capture_completeness",
        caller_input=caller_input,
        hidden_context=hidden_context,
        expected_next_action=expected_next_action,
        observed_next_action=observed_next_action,
        conversation_text=conversation_text,
        expected_route=expected_route,
        observed_route=observed_route,
    )


def build_judge_system_prompt(judge_name: str) -> str:
    if judge_name == "clarification_quality":
        return (
            "You are an evaluator for an intake orchestrator. "
            "Judge whether the agent asked a necessary and timely clarifying question. "
            "Use the full conversation and trace context. "
            "Return valid JSON only with keys: score, label, rationale, details. "
            "Score must be a number from 0.0 to 1.0. "
            "Label must be one of: pass, partial, fail. "
            "Pass when ambiguity is handled well, partial when the behavior is directionally okay but imperfect, "
            "and fail when the agent asks too late, asks unnecessarily, or routes too early."
        )
    if judge_name == "issue_capture_completeness":
        return (
            "You are an evaluator for an intake orchestrator. "
            "Judge whether the full conversation captured enough details to justify the route. "
            "Use the full conversation and trace context. "
            "Return valid JSON only with keys: score, label, rationale, details. "
            "Score must be a number from 0.0 to 1.0. "
            "Label must be one of: pass, partial, fail. "
            "Pass when the conversation contains the concrete issue details needed for routing, "
            "partial when most information is present but one key detail is missing, "
            "and fail when the handoff or route is still under-specified."
        )
    raise ValueError(f"Unknown judge name: {judge_name}")


def build_judge_user_prompt(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2)


def serialize_trace_for_judge(run: Any) -> str:
    lines: list[str] = []
    _append_run_trace(lines, run, depth=0)
    return "\n".join(lines).strip()


def parse_judge_result(raw: Any) -> dict[str, Any]:
    parsed = raw
    if isinstance(raw, IntakeJudgeResult):
        parsed = asdict(raw)
    elif isinstance(raw, str):
        parsed = _parse_json_like(raw)

    if not isinstance(parsed, dict):
        return {
            "score": 0.0,
            "label": "fail",
            "rationale": "Judge output was malformed or unavailable.",
            "details": {"raw": raw},
        }

    score = _coerce_score(parsed.get("score"), parsed.get("label"))
    label = _coerce_label(parsed.get("label"), score)
    rationale = str(parsed.get("rationale") or parsed.get("reason") or "").strip()
    if not rationale:
        rationale = "Judge output did not include a usable rationale."

    details = {k: v for k, v in parsed.items() if k not in {"score", "label", "rationale"}}
    return {
        "score": score,
        "label": label,
        "rationale": rationale,
        "details": details or None,
    }


def _build_base_payload(
    *,
    case_id: str,
    judge_name: str,
    caller_input: str,
    hidden_context: str,
    expected_next_action: str,
    observed_next_action: str,
    conversation_text: str,
    expected_route: str | None,
    observed_route: str | None,
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "judge_name": judge_name,
        "caller_input": caller_input,
        "hidden_context": hidden_context,
        "expected_next_action": expected_next_action,
        "observed_next_action": observed_next_action,
        "expected_route": expected_route,
        "observed_route": observed_route,
        "conversation_text": conversation_text,
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }


def _append_run_trace(lines: list[str], run: Any, depth: int) -> None:
    indent = "  " * depth
    if run is None:
        return
    name = str(getattr(run, "name", "run") or "run")
    run_type = str(getattr(run, "run_type", "") or "")
    run_id = getattr(run, "id", None)
    line = f"{indent}- {name}"
    if run_type:
        line += f" [{run_type}]"
    if run_id:
        line += f" id={run_id}"
    lines.append(line)

    start_time = getattr(run, "start_time", None)
    end_time = getattr(run, "end_time", None)
    if start_time or end_time:
        lines.append(f"{indent}  time: {start_time!s} -> {end_time!s}")

    inputs = getattr(run, "inputs", None)
    outputs = getattr(run, "outputs", None)
    error = getattr(run, "error", None)
    if inputs is not None:
        lines.append(f"{indent}  inputs: {_safe_json(inputs)}")
    if outputs is not None:
        lines.append(f"{indent}  outputs: {_safe_json(outputs)}")
    if error:
        lines.append(f"{indent}  error: {error}")

    child_runs = getattr(run, "child_runs", None) or []
    for child in child_runs:
        _append_run_trace(lines, child, depth + 1)


def _safe_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    except TypeError:
        return json.dumps(_stringify(value), ensure_ascii=True, sort_keys=True)


def _stringify(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _stringify(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_stringify(item) for item in value]
    if isinstance(value, tuple):
        return [_stringify(item) for item in value]
    if isinstance(value, set):
        return sorted(_stringify(item) for item in value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _parse_json_like(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _coerce_score(score: Any, label: Any) -> float:
    try:
        value = float(score)
    except (TypeError, ValueError):
        label_value = str(label or "").strip().lower()
        if label_value == "pass":
            return 1.0
        if label_value == "partial":
            return 0.5
        return 0.0
    return max(0.0, min(1.0, value))


def _coerce_label(label: Any, score: float) -> str:
    candidate = str(label or "").strip().lower()
    if candidate in VALID_JUDGE_LABELS:
        return candidate
    if score >= 0.75:
        return "pass"
    if score >= 0.25:
        return "partial"
    return "fail"
