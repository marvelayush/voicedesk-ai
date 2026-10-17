# Intake LLM Judge Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an LLM-as-judge layer to the Week 3 Intake Orchestrator evaluation so we can score clarification quality and issue capture completeness from the full trace/conversation, while keeping route correctness code-based.

**Architecture:** Keep the current LangSmith batch evaluation as the entry point, but extend it with two rubric-based judge metrics that inspect the full run trace rather than only the final output. Route correctness remains an exact-match evaluator so deterministic scoring stays deterministic. The judge should be calibrated with a small reviewed subset first, then run over the full golden dataset, with scores and rationales stored in LangSmith for trace-level inspection.

**Tech Stack:** Python, LangSmith SDK, Nebius OpenAI-compatible chat endpoint, openpyxl for the dataset workbook, pytest for judge/parser tests.

---

## Problem Statement

The current evaluation already measures route correctness and intake safety, but it does not score the quality of the conversation itself. For intake routing, that matters because the agent can get the final route right while still:

- asking a clarifying question too late
- asking an unnecessary question when the issue is already specific enough
- failing to capture the details needed to justify the route

We need judge metrics that reflect the user outcome more directly than exact route alone.

## Desired Metrics

Keep the existing exact-match routing metric, and add two new LLM-judged metrics:

1. **Clarification quality**
   - Does the agent ask a necessary and timely clarifying question when the caller is ambiguous?
   - Does it avoid asking unnecessary clarifying questions when the issue is already specific?

2. **Issue capture completeness**
   - Does the full conversation capture the key details needed to support the final routing decision?
   - Did the agent gather enough information before handoff?

Route correctness stays code-based and is not moved to an LLM judge.

## Proposed Scoring Scheme

Use a three-level rubric for both judge metrics:

- `pass` = the behavior matches the rubric and supports the correct support flow
- `partial` = the behavior is directionally okay but incomplete, late, or slightly misaligned
- `fail` = the behavior is clearly wrong or harmful to the support flow

Map the rubric to numeric scores for aggregation:

- `pass` -> `1.0`
- `partial` -> `0.5`
- `fail` -> `0.0`

This keeps the judge readable for humans and still usable for simple summary stats.

## Data To Judge

The judge should inspect the full trace/conversation for each case, not just the last assistant message.

The judge input should include:

- caller input
- hidden context
- expected route and expected next action
- observed route and observed next action
- the full conversation or trace transcript when available
- the final output payload from the intake agent

If the current trace does not expose enough conversation detail, the implementation should add a compact trace serialization helper so the judge always gets the same structured text.

## Files and Responsibilities

- `scripts/langsmith_baseline.py`
  - keeps the dataset upload and LangSmith batch runner
  - adds the new judge evaluators to the eval list
  - builds the serialized judge input from each run and example
  - keeps the summary metrics and comparison output

- `src/nebius_client.py`
  - provides the shared Nebius chat helper used for judge calls
  - accepts a prompt + structured judge payload and returns parsed JSON
  - stays the single place for model access and token accounting

- `docs/evaluation.md`
  - records the judge rubric at a high level
  - records the judge calibration subset and any known caveats
  - logs the before/after metric values once the judge is working

- `tests/evaluation/test_intake_judges.py`
  - verifies prompt serialization, score parsing, and fallback behavior
  - checks that malformed judge output does not break the eval runner

## Judge Prompt Design

Use two separate judge prompts, one for each soft metric, so each rubric stays focused.

### Clarification Quality Judge

Judge question:

- Did the agent ask a necessary and timely clarifying question?

Rubric cues:

- `pass` when ambiguity is real and the agent asks a targeted clarifying question before routing
- `partial` when the agent eventually clarifies but is a bit late or a bit vague
- `fail` when the agent routes too early or asks a needless question on a specific issue

### Issue Capture Completeness Judge

Judge question:

- Did the full conversation capture enough information to justify the route?

Rubric cues:

- `pass` when the key issue details are explicit enough for the next support step
- `partial` when the conversation gets most of the way there but misses one important detail
- `fail` when the conversation is still too thin or the handoff is premature

Each judge should return structured JSON with:

- `score`
- `label`
- `rationale`
- `missing_information` or `better_alternative_action`

## Calibration Plan

Before scoring the full dataset, manually review a small calibration slice of cases:

- 5 to 8 cases
- include at least one happy path, one ambiguous intake case, one known failure, and one adversarial case

Use that slice to check whether the judge labels match the human expectation. If the judge disagrees with obvious cases, tighten the rubric wording before running the full eval.

## Failure Handling

Judge failures should not break the evaluation run.

If the judge model output is malformed or missing fields:

- fall back to `partial` or `fail` according to a conservative parser rule
- record the malformed response in the trace metadata
- keep the run moving so one bad judge response does not destroy the batch

## Success Criteria

This work is done when:

- route correctness still scores through exact match
- clarification quality and issue capture completeness are scored with LLM judges
- the judges use full trace/conversation context
- judge outputs are visible in LangSmith
- the evaluation summary can report baseline and post-improvement deltas for all three metrics

## Rollout Plan

1. Add the judge prompt helpers and JSON parser.
2. Wire the new judge evaluators into the LangSmith batch run.
3. Run the 5 to 8 case calibration slice.
4. Adjust rubric wording if the judge disagrees with obvious human labels.
5. Run the full golden dataset.
6. Update `docs/evaluation.md` with judge metrics and observations.

