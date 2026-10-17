# Promptfoo Stress Testing

This repo includes a repeatable Promptfoo harness for VoiceDesk AI, the multi-agent IT support voice assistant.

Prerequisite:

- Promptfoo runs on Node.js. If `promptfoo`, `node`, or `npm` are not recognized, install Node.js first, then rerun the commands below.

What it does:

- replays the same attack families used in the manual stress-test report
- checks that the assistant refuses prompt injection, jailbreaking, role override, authority-pressure, PII extraction, workflow abuse, obfuscation, and crescendo attempts
- flags any visible internal-instruction leakage before it reaches the report or UI
- gives a quick regression check after guardrail changes

Files:

- [`promptfooconfig.yaml`](../promptfooconfig.yaml)
- [`promptfoo/guardrail_target.py`](../promptfoo/guardrail_target.py)
- [`promptfoo/stress_test_cases.yaml`](../promptfoo/stress_test_cases.yaml)
- [`src/promptfoo_harness.py`](../src/promptfoo_harness.py)
- [`api.py`](../api.py)
- [`docs/stress_test_demo_report.md`](./stress_test_demo_report.md)

Run it locally:

```bash
uvicorn api:app --reload
promptfoo eval -c promptfooconfig.yaml
```

If you prefer `npx`:

```bash
npx promptfoo@latest eval -c promptfooconfig.yaml
```

If `promptfoo` is still not recognized after installing Node.js, use the `npx` form above or install it globally with `npm install -g promptfoo`.

The harness uses a local HTTP endpoint backed by the same safe refusal and intake-gating logic the demo should show in production. That makes the stress test deterministic and easy to rerun after code changes.

Recommended workflow:

1. Make a guardrail change.
2. Run the Promptfoo suite.
3. Compare pass/fail results against the manual report.
4. Re-run the manual red-team screenshots only when you need presentation-quality evidence.

This Promptfoo suite is a complement to the manual report, not a replacement for it.
