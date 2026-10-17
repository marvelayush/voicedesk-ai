# Intake LLM Judge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add LLM-as-judge metrics for clarification quality and issue capture completeness to the Week 3 intake evaluation, using full conversation/trace context in LangSmith while preserving exact-match route scoring.

**Architecture:** Keep the existing batch eval runner as the orchestration point, but move judge-specific prompt construction and response parsing into a focused helper module so the runner stays readable. Use a shared Nebius JSON-chat helper for all judge calls, return structured scores with rationale, and keep route correctness code-based. Add a small calibration slice first so the judge rubric can be checked against a few hand-reviewed cases before full dataset scoring.

**Tech Stack:** Python, LangSmith SDK, Nebius OpenAI-compatible API, openpyxl, pytest.

---

### Task 1: Add a dedicated judge helper module

**Files:**
- Create: `src/intake_judges.py`
- Create: `tests/test_intake_judges.py`

- [ ] **Step 1: Write the failing test**

```python
from src.intake_judges import build_clarification_judge_payload, build_issue_capture_judge_payload, parse_judge_result

def test_parse_judge_result_accepts_valid_json():
    raw = {
        "score": 1.0,
        "label": "pass",
        "rationale": "The agent asked a timely clarifying question.",
    }
    result = parse_judge_result(raw)
    assert result["score"] == 1.0
    assert result["label"] == "pass"

def test_parse_judge_result_falls_back_on_malformed_payload():
    result = parse_judge_result({"unexpected": "value"})
    assert result["score"] == 0.0
    assert result["label"] in {"partial", "fail"}

def test_build_clarification_judge_payload_includes_full_trace():
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_intake_judges.py -v`
Expected: import errors or assertion failures until the module exists.

- [ ] **Step 3: Write minimal implementation**

Implement:
- `IntakeJudgeResult` dataclass with `score`, `label`, `rationale`, and optional `details`
- `build_clarification_judge_payload(...)`
- `build_issue_capture_judge_payload(...)`
- `parse_judge_result(...)` with conservative fallback behavior
- `serialize_trace_for_judge(...)` so the full conversation/trace is consistently formatted

Use a stable JSON shape:

```python
{
    "case_id": "...",
    "caller_input": "...",
    "hidden_context": "...",
    "expected_next_action": "...",
    "expected_route": "...",
    "observed_next_action": "...",
    "observed_route": "...",
    "conversation_text": "...",
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_intake_judges.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/intake_judges.py tests/test_intake_judges.py
git commit -m "feat: add intake judge payload helpers"
```

### Task 2: Add Nebius judge-scoring support

**Files:**
- Modify: `src/nebius_client.py`
- Create: `tests/test_nebius_client.py`

- [ ] **Step 1: Write the failing test**

Add tests that prove:

```python
from src.nebius_client import NebiusClient

def test_nebius_client_returns_fallback_when_disabled():
    client = NebiusClient()
    result = client.score_intake_judge("clarification_quality", {"case_id": "H11"}, fallback={"score": 0.0, "label": "fail"})
    assert result["score"] == 0.0
    assert result["label"] == "fail"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_intake_judges.py tests/test_nebius_client.py -v`
Expected: the new judge-scoring call is missing.

- [ ] **Step 3: Write minimal implementation**

Add one generic method to `NebiusClient`:

```python
def score_intake_judge(self, judge_name: str, payload: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    ...
```

Behavior:
- use a judge-specific system prompt
- send the serialized payload as JSON text
- expect JSON output with `score`, `label`, `rationale`
- return fallback values when the model is unavailable or returns malformed data
- keep `temperature=0.0`
- preserve token usage in the response dict

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_intake_judges.py tests/test_nebius_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/nebius_client.py tests/test_nebius_client.py
git commit -m "feat: add nebius intake judge scoring"
```

### Task 3: Wire the new judges into the LangSmith eval runner

**Files:**
- Modify: `scripts/langsmith_baseline.py`
- Create: `tests/test_langsmith_baseline.py`

- [ ] **Step 1: Write the failing test**

Add a focused test that imports the runner helpers and verifies the new evaluators are present:

```python
from scripts.langsmith_baseline import build_evaluators

def test_build_evaluators_includes_route_and_judge_metrics():
    evaluators = build_evaluators()
    names = {e.__name__ for e in evaluators}
    assert "route_exact_match" in names
    assert "clarification_quality" in names
    assert "issue_capture_completeness" in names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_intake_judges.py tests/test_nebius_client.py tests/test_langsmith_baseline.py -v`
Expected: evaluator factory not implemented yet.

- [ ] **Step 3: Write minimal implementation**

Refactor the runner so it:
- serializes the full run trace or conversation for each example
- feeds that text into the two new judge evaluators
- keeps `route_exact_match` code-based
- adds the judge metrics to the summary printout
- preserves current dataset upload behavior and experiment naming

Use LangSmith evaluators in this order:
- route correctness
- clarification quality
- issue capture completeness

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_langsmith_baseline.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/langsmith_baseline.py tests/test_langsmith_baseline.py
git commit -m "feat: wire intake judges into langsmith eval"
```

### Task 4: Document the judge rubric and calibration workflow

**Files:**
- Modify: `docs/evaluation.md`
- Modify: `README.md`

- [ ] **Step 1: Write the failing test**

No code test is needed here. The acceptance criterion is that the docs clearly describe:
- the two LLM judge metrics
- the full-trace input requirement
- the calibration slice
- the fallback rule for malformed judge output

- [ ] **Step 2: Implement the doc updates**

Add a short section in `docs/evaluation.md` that explains:
- what the judge scores
- why full trace context matters
- how the calibration slice is used
- how to interpret `pass`, `partial`, and `fail`

Add a brief README note that the eval now includes LLM-as-judge metrics for the intake orchestrator.

- [ ] **Step 3: Review the wording**

Confirm the docs do not overclaim:
- route correctness is still exact-match
- judge scores are rubric-based, not ground truth
- full-trace context is required for the soft metrics

- [ ] **Step 4: Commit**

```bash
git add docs/evaluation.md README.md
git commit -m "docs: describe intake llm judge evaluation"
```

### Task 5: Run calibration and full evaluation

**Files:**
- No code changes unless calibration exposes a rubric bug

- [ ] **Step 1: Run the calibration slice**

Run the first 5 to 8 hand-reviewed cases through the new judge path and compare the judge outputs against human expectation.

Expected command:

```bash
py scripts/langsmith_baseline.py --mode llm --limit 8
```

Expected result:
- judge metrics are emitted
- obvious cases score as expected
- any mismatch is explainable and localizable to the rubric wording

- [ ] **Step 2: Adjust the rubric if needed**

If a judge is too lenient or too strict, tighten the prompt wording in `src/nebius_client.py` or `src/intake_judges.py`, then rerun the calibration slice.

- [ ] **Step 3: Run the full golden dataset**

Run:

```bash
py scripts/langsmith_baseline.py --mode llm
```

Expected result:
- all three metrics appear in the LangSmith experiment
- the comparison view shows baseline vs post-improvement values
- the new judge metrics have meaningful, non-zero distributions

- [ ] **Step 4: Record the results**

Update `docs/evaluation.md` with:
- the calibration outcome
- the final judge metric values
- any disagreements found during spot-checking
- the measured delta from baseline

- [ ] **Step 5: Commit**

```bash
git add docs/evaluation.md src/intake_judges.py src/nebius_client.py scripts/langsmith_baseline.py
git commit -m "feat: add llm judges for intake evaluation"
```

## Self-Review Checklist

- Route correctness remains code-based exact match.
- Clarification quality and issue capture completeness use the full trace or conversation.
- Judge outputs are parsed conservatively and do not break the batch run.
- Calibration happens before the full dataset run.
- Docs explain how to read the judge scores and their limits.
