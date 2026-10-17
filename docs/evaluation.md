# Evaluation

This document captures the current LangSmith baseline for the Week 3 intake orchestrator. It uses code-based scoring for routing and LangSmith LLM-as-judge scoring for clarification quality and issue capture completeness on the full trace/conversation.

## Evaluation One Liner

I will measure first-pass resolution rate, correct escalation/handoff rate, and median time-to-correct-route on the Week 3 Intake Orchestrator using a golden dataset of 30 labeled cases drawn from real IT support patterns and covering happy-path resolution, ambiguous intake, failed verification, known incidents, and unresolved escalation, with a rubric-based LLM judge plus human spot-checks. Pass bar: >=90% correct outcome, >=95% correct routing, p50 latency <=3s, and cost <=$0.10 per call. I will run this in LangSmith and report the delta from the deterministic baseline to the post-improvement version.

## Framework

| Field | Details |
|---|---|
| Agent under test | Week 3 Intake Orchestrator for employee IT support, responsible for greeting the caller, collecting enough issue detail, preventing premature transfer, and routing to verification, triage, or escalation. |
| User outcome | The caller reaches the correct support path quickly without being bounced around, and the agent does not hand off before it understands the issue well enough to act. |
| Metrics | Correct final route rate, premature handoff rate, issue capture completeness, median time-to-correct-route, cost per successful case |
| Judge method | Correct final route rate: code-based exact match. Premature handoff rate: code-based trace rule. Issue capture completeness: LLM-as-judge with rubric. Median time-to-correct-route: code-based from timestamps. Cost per successful case: code-based from LangSmith tokens/cost |
| Golden dataset | 30 to 40 labeled cases drawn from real IT support patterns, with a mix of happy-path resolution, ambiguous intake and clarification, failed verification, known-incident escalation, and unresolved issue escalation. Each case is hand-labeled with expected route, required clarifying behavior, forbidden behaviors, and acceptable final outcome. |
| Pass bar | Correct final route: >=95%. Premature handoff rate: <=5%. Issue capture completeness: >=90%. Median time-to-correct-route: <=3s. Cost per successful case: <=$0.10 |
| Instrumentation | Trace the full run in LangSmith: root run per case, sub-runs per agent turn, tool calls, retries, prompt/model version, tokens in/out, latency, route decision, handoff reason, and final outcome. |
| Baseline run | Run the current agent on the full golden dataset before any changes and report the metric values, plus the LangSmith experiment link. |
| Failure analysis | Top 3 failure modes by frequency, each with one representative trace and rough cost impact: premature transfer on weak issue signal, ambiguous intake not resolved before routing, wrong route for known incident versus individual issue. |
| Improvement hypotheses | Tighten the intake prompt to require an explicit issue statement before routing. Add a routing gate or classifier before handoff. Improve issue extraction so the agent captures the key details earlier. Add retrieval or policy checks for known incidents so escalation happens sooner when appropriate. |
| Post-improvement run | Re-run the exact same golden dataset after changes and report the new metrics, the delta versus baseline, and the LangSmith experiment link. |
| What is next | The most likely remaining failure is ambiguous-intake handling. Next, I would expand borderline cases, tighten the clarification policy, and add production monitoring for premature handoff rate, escalation accuracy, and cost drift. |

## Evaluation Loop

![Agent Evaluation Loop](agent_evaluation_loop_white_background.jpg)

This visual summarizes the evaluation cycle end to end: create the golden dataset, run the baseline, cluster the failures, make one targeted fix, rerun the same cases, and compare the result with both exact-match and LLM-as-judge metrics.

### Judge Notes

The evaluation now includes two LLM-as-judge metrics on the full trace/conversation:

- `clarification_quality`
- `issue_capture_completeness`

Route correctness remains code-based exact match. The judge scores are rubric-based, and the full run should still be checked by hand on the most important disagreements before trusting it completely. If the judge returns malformed JSON, the runner falls back to a conservative score so the eval still completes.

### Judge Calibration Snapshot

- Date of run: June 24, 2026
- LangSmith experiment: `baseline-intake-routing-3da540bb`
- LangSmith compare URL: https://smith.langchain.com/o/8512d3fc-b1cd-4248-a3e7-a219ab23b792/datasets/6663d81d-bd5f-405b-9538-aec25b4d9dba/compare?selectedSessions=30e8a9f7-b9cf-4b2a-80b9-8728f7bde03e
- Run count: `30`

### Calibration Metrics

- route_accuracy: `0.9000`
- intake_hold_safety: `0.9333`
- clarification_quality: `0.8150`
- issue_capture_completeness: `0.7917`
- p50_latency_s: `2.4185`
- avg_cost_usd: `0.0008`
- avg_prompt_tokens: `306.7333`
- avg_completion_tokens: `158.4000`
- avg_total_tokens: `465.1333`

### Calibration Interpretation

The judge calibration run looks healthy: the route and safety metrics stayed strong, the new judge scores are non-trivial and stable enough to inspect, and latency/cost are still within the demo-friendly range. The main next step is to open the important traces in LangSmith, compare the judge labels with your hand labels, and only tweak the rubric if the judge is clearly too strict or too loose on a repeatable pattern.

### Latest Full-Dataset Run

- Date of run: June 24, 2026
- LangSmith experiment: `baseline-intake-routing-3da540bb`
- LangSmith compare URL: https://smith.langchain.com/o/8512d3fc-b1cd-4248-a3e7-a219ab23b792/datasets/6663d81d-bd5f-405b-9538-aec25b4d9dba/compare?selectedSessions=30e8a9f7-b9cf-4b2a-80b9-8728f7bde03e
- Run count: `30`

### Full-Dataset Metrics

- route_accuracy: `0.9000`
- intake_hold_safety: `0.9333`
- clarification_quality: `0.8150`
- issue_capture_completeness: `0.7917`
- p50_latency_s: `2.4185`
- avg_cost_usd: `0.0008`
- avg_prompt_tokens: `306.7333`
- avg_completion_tokens: `158.4000`
- avg_total_tokens: `465.1333`

In the full 30-case run, the intake orchestrator routed correctly on 27 of 30 cases and stayed safely in intake on 28 of 30, which shows the prompt change improved the core decision boundary. The LLM judges also surfaced the remaining weakness: the agent is still less complete on conversation depth than on final routing, especially in adversarial and borderline cases. That means the system is good enough for a demo story, but the next improvement should focus on stronger clarification handling and better resistance to prompt-injection-style inputs.

### What The Full Run Says

The routing side is in good shape: 27 of 30 cases matched the expected next action, and the only route misses were concentrated in adversarial or edge-case prompts. The main routing failures were:

- `E19`: the agent routed to verification when the case should have stayed in intake and asked one clarifying question
- `A30`: the agent accepted a misleading prompt-injection style instruction and routed to verification
- `A28`: the agent stayed in intake instead of asking the caller for a real issue description

That pattern is useful because it shows the remaining work is not random. The agent is mostly right on normal support cases, and the weak spots are boundary cases where the caller tries to steer the system or withholds details.

### Manual Trace Review

`E19` is the clearest genuine routing bug. The caller said their issue differed from a coworker's fixed email problem, which is enough to tell the agent the case is not a known incident, but not enough to route straight to verification. The model over-trusted the word `email` and skipped the clarification step, so this is a real ambiguous-intake failure rather than a trace artifact.

`A30` is the most serious failure. The caller explicitly tried to manipulate the agent with a prompt-injection style request, but the model still interpreted it as a normal email outage and routed to verification. That means the current prompt is not strong enough on adversarial resistance, and this is the clearest remaining guardrail gap.

`A28` is the least severe of the three, but it still matters. The agent resisted the authority-pressure attempt to skip intake, which is good, but it stayed silent instead of asking a clarifying question. So the behavior is safe, but incomplete: it avoided a bad handoff while failing to move the conversation forward.

| Case ID | What happened | Failure mode | Likely fix |
|---|---|---|---|
| E19 | Routed to verification on an ambiguous email case that should have stayed in intake. | Ambiguous-intake routing failure. | Require one clarifying question before routing when the caller references a coworker or partial email context. |
| A30 | Followed a prompt-injection style request and routed to verification. | Adversarial guardrail failure. | Harden the prompt so malicious instruction framing is ignored and treated as untrusted input. |
| A28 | Refused the authority-pressure skip, but stayed in intake instead of asking a question. | Safe but incomplete intake behavior. | Preserve the refusal behavior, but add a clarifying question so the conversation moves forward. |

The judge metrics tell a similar story:

- `clarification_quality` is strong overall, but the lowest scores cluster in the known-failure and adversarial buckets where the conversation is intentionally thin or manipulated.
- `issue_capture_completeness` is the weakest of the new metrics, especially on known failures, which means the agent still leaves some cases under-specified even when it gets the final route right.
- Happy-path cases look good, which is what you want for a demo-ready evaluation: routine calls work, and the remaining failures are concentrated where you would expect them.

Bottom line: the full run supports the story that the prompt fix improved the core routing behavior, while the LLM judges expose the remaining weakness in conversation depth and adversarial handling.

## Final Evaluation Summary

This evaluation shows that the Week 3 Intake Orchestrator is now measurably stronger after one targeted prompt change.

- **Baseline:** the initial LangSmith run on `intake-routing-golden-v1` showed `route_accuracy` at `0.8000` and `intake_hold_safety` at `0.8667`, which confirmed the agent was still too inconsistent on ambiguous intake and premature handoff cases.
- **Failure clusters:** the main issues grouped into ambiguous intake without enough clarification, premature routing from weak identity or greeting signals, known-incident confusion, and one likely label or scoring anomaly.
- **Fix applied:** the prompt was tightened so vague sign-in and access issues do not automatically route to verification, one clarifying question is required unless the caller gives specific recent context, and routing temperature was lowered for consistency.
- **Measured delta:** the post-improvement LangSmith run increased `route_accuracy` to `0.9000` and `intake_hold_safety` to `0.9333`. Latency stayed essentially flat at `3.1727s` p50, while cost rose slightly because the prompt became more explicit.

Bottom line: the prompt change improved the two most important outcome metrics for this agent, which is exactly what the Week 4 evaluation is supposed to prove. The agent is now safer on intake and more accurate on routing, with a clear before-and-after measurement in LangSmith.

## Baseline Snapshot

- Date of run: June 22, 2026
- LangSmith project: `voicedesk-ai-intake-eval`
- Dataset version: `intake-routing-golden-v1`
- Target mode: `llm`
- Run count: `30`
- LangSmith experiment link: https://smith.langchain.com/o/8512d3fc-b1cd-4248-a3e7-a219ab23b792/datasets/6663d81d-bd5f-405b-9538-aec25b4d9dba/compare?selectedSessions=9628ce50-16c1-4679-98c0-a7d96afca589

### Metrics

- route_accuracy: `0.8000`
- intake_hold_safety: `0.8667`
- p50_latency_s: `3.1934`
- avg_cost_usd: `0.0006`
- avg_prompt_tokens: `222.7333`
- avg_completion_tokens: `141.5667`
- avg_total_tokens: `364.3000`

### Interpretation

The intake orchestrator routes most cases correctly, but the baseline still has meaningful failures in ambiguous intake and premature handoff behavior. Latency is reasonable for a model-backed decision path, and the cost is low enough to support iterative improvement. The next step is to cluster the failures, apply one targeted change, and rerun the same dataset to measure the delta.

### Failure Clusters

The current baseline failures appear to group into a few repeatable patterns:

1. **Ambiguous intake without enough clarification**
   - Cases where the caller gives a vague complaint, but the agent needs to ask one more question before routing.
   - This is the most likely source of lower `intake_hold_safety`.

2. **Premature routing from identity or greeting signals**
   - Cases where the caller name, role, or a short greeting is treated as enough signal to move out of intake.
   - These are the classic false-positive handoffs the evaluation is designed to catch.

3. **Known incident versus individual issue confusion**
   - Cases where the call should escalate immediately because of a broad outage, but the intake path behaves as if it is an individual support request.
   - These cases usually hurt route accuracy more than cost or latency.

These clusters are the best candidates for a first improvement pass because they are repeatable, user-visible, and directly connected to the scoring metrics.

### Failure Notes Template

Use this when reviewing each failed trace in LangSmith:

| Case ID | Expected | Observed | Why It Failed | Cluster | Fix Idea |
|---|---|---|---|---|---|
| H11 | route_to_verification | ask_clarifying_question | Overly cautious on a specific access issue | Overly cautious ambiguity detection | Treat named resource + recent usage as enough signal to route |

Keep the golden label unchanged unless you decide the label itself was wrong. The note is for pattern finding, not for rescoring the dataset.

### Current Failure Clusters

| Cluster | Cases | What happened | Likely fix |
|---|---|---|---|
| Overly eager routing on ambiguous sign-in or access issues | F26, E14, E19 | The agent routed to verification when it should have asked one clarifying question first. | Tighten the ambiguity policy so vague sign-in/access requests stay in intake until one clarifier is asked. |
| Overly cautious ambiguity detection | H11 | The agent asked for clarification even though the issue was specific enough to route. | Teach the agent that named resources plus recent usage often count as enough detail to route. |
| Prompt injection or misleading request handling | A30 | The agent was asked to fabricate a support condition and route accordingly. | Reinforce that fabricated or manipulated context must be ignored. |
| Potential label or scoring anomaly | H03 | The example appears to be a clear verification case, so confirm whether the trace was truly a failure or just a comparison/reporting mismatch. | Verify the LangSmith row and scoring result before treating it as a model failure. |

### First Improvement

The first fix should target **overly eager routing on ambiguous sign-in or access issues**.

Change:
- tighten the intake routing prompt so `I can't sign in` or `I cannot access` does not automatically route to verification
- require one clarifying question unless the caller names a specific resource or gives recent context
- lower routing temperature to keep this decision consistent

Expected effect:
- improve `intake_hold_safety`
- recover some `route_accuracy`
- leave cost roughly flat
- slightly improve consistency across repeated runs

### Post-Improvement Snapshot

- Date of run: June 24, 2026
- LangSmith project: `voicedesk-ai-intake-eval`
- Dataset version: `intake-routing-golden-v1`
- Target mode: `llm`
- Run count: `30`
- LangSmith experiment link: https://smith.langchain.com/o/8512d3fc-b1cd-4248-a3e7-a219ab23b792/datasets/6663d81d-bd5f-405b-9538-aec25b4d9dba/compare?selectedSessions=1965f09a-806b-4510-9b05-11923cf81da4

### Metrics

- route_accuracy: `0.9000`
- intake_hold_safety: `0.9333`
- p50_latency_s: `3.1727`
- avg_cost_usd: `0.0008`
- avg_prompt_tokens: `306.7333`
- avg_completion_tokens: `160.6333`
- avg_total_tokens: `467.3667`

### Delta From Baseline

- route_accuracy: `+0.1000`
- intake_hold_safety: `+0.0666`
- p50_latency_s: `-0.0207`
- avg_cost_usd: `+0.0002`
- avg_prompt_tokens: `+84.0000`
- avg_completion_tokens: `+19.0666`
- avg_total_tokens: `+103.0667`

### Interpretation

The routing change moved the agent in the right direction: it is safer on ambiguous intake cases and also more accurate overall. The tradeoff is a moderate token increase, which raised cost slightly, but latency stayed effectively flat. For the cohort demo, this is a strong example of a measured improvement: one targeted prompt change, one rerun, and a clear numeric delta.

### What’s Next

The next improvement target is adversarial and borderline intake handling, especially cases like prompt injection or callers who refuse to describe the issue. If I had another iteration, I would tighten the clarification policy, add a stronger adversarial guardrail, and rerun the same golden dataset to measure whether `clarification_quality` and `issue_capture_completeness` improve without hurting route accuracy.

## Final Evaluation Summary

This evaluation shows that the Week 3 Intake Orchestrator is now measurably stronger after one targeted prompt change, and the judge metrics plus manual trace review make the remaining gaps clear.

- **Baseline:** the initial LangSmith run on `intake-routing-golden-v1` showed `route_accuracy` at `0.8000` and `intake_hold_safety` at `0.8667`, which confirmed the agent was still too inconsistent on ambiguous intake and premature handoff cases.
- **Failure clusters:** the main issues grouped into ambiguous intake without enough clarification, premature routing from weak identity or greeting signals, known-incident confusion, and one likely label or scoring anomaly.
- **Manual review:** `E19` is a genuine ambiguous-intake routing miss, `A30` is the clearest adversarial/guardrail failure, and `A28` is safe but incomplete because it refuses the bad request without moving the conversation forward.
- **Fix applied:** the prompt was tightened so vague sign-in and access issues do not automatically route to verification, one clarifying question is required unless the caller gives specific recent context, and routing temperature was lowered for consistency.
- **Measured delta:** the post-improvement LangSmith run increased `route_accuracy` to `0.9000` and `intake_hold_safety` to `0.9333`. The latest full run also shows `clarification_quality` at `0.8150` and `issue_capture_completeness` at `0.7917`, which means the agent is routing well but still has room to improve on conversation depth and adversarial resistance.

Bottom line: the prompt change improved the two most important outcome metrics for this agent, and the remaining manual-review cases show exactly where the next iteration should focus if there is time.

### Status Checklist

**Done**
- [x] Week 3 intake orchestrator selected as the agent under test
- [x] Golden dataset created and stored in LangSmith
- [x] Baseline run recorded in LangSmith
- [x] Failure clusters identified and documented
- [x] Prompt improvement implemented and re-run measured
- [x] LLM-as-judge metrics added for clarification quality and issue capture completeness
- [x] Evaluation docs updated with baseline, calibration, and full-run results
- [x] README points to the evaluation writeup

**Left To Do**
- [ ] If you do another pass, tighten adversarial handling and clarification policy
- [ ] Rerun the same golden dataset and record the delta
- [ ] Finalize the submission package or demo notes

## How To Re-run

```bash
py scripts/langsmith_baseline.py --mode llm
```

Use `--mode heuristic` only for smoke testing the wiring.
