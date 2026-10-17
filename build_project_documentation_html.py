from __future__ import annotations

from pathlib import Path
import html


OUT_PATH = Path("docs") / "multi_agent_it_support_voice_demo_documentation.html"


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def section(title: str, body: str) -> str:
    return f"""
    <section class="section">
      <h2>{esc(title)}</h2>
      {body}
    </section>
    """


def table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{esc(cell).replace(chr(10), '<br>')}</td>" for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")
    return f"""
    <table>
      <thead><tr>{head}</tr></thead>
      <tbody>
        {''.join(body_rows)}
      </tbody>
    </table>
    """


def code_block(lines: list[str]) -> str:
    return "<pre>" + esc("\n".join(lines)) + "</pre>"


def bullet_list(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"


def box(title: str, text: str) -> str:
    return f"""
    <div class="placeholder">
      <div class="placeholder-title">{esc(title)}</div>
      <div class="placeholder-copy">{esc(text)}</div>
    </div>
    """


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    html_doc = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>VoiceDesk AI Documentation</title>
  <style>
    body {{
      font-family: Arial, Helvetica, sans-serif;
      color: #1f1f1f;
      margin: 48px;
      line-height: 1.45;
      font-size: 11pt;
    }}
    h1 {{
      font-size: 26pt;
      margin: 0 0 6px 0;
      font-weight: normal;
      color: #000;
    }}
    .subtitle {{
      color: #666;
      margin-bottom: 14px;
    }}
    h2 {{
      font-size: 16pt;
      color: #2e74b5;
      margin: 20px 0 8px;
    }}
    h3 {{
      font-size: 13pt;
      color: #1f4d78;
      margin: 14px 0 6px;
    }}
    p {{ margin: 0 0 8px 0; }}
    ul {{ margin: 4px 0 8px 20px; }}
    li {{ margin: 0 0 4px 0; }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin: 8px 0 12px 0;
      font-size: 10.5pt;
    }}
    th, td {{
      border: 1px solid #c6cfdb;
      padding: 8px 10px;
      vertical-align: top;
      text-align: left;
    }}
    th {{
      background: #e8eef5;
      font-weight: bold;
    }}
    pre {{
      background: #f4f6f9;
      border: 1px solid #d8dee8;
      padding: 12px;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: "Courier New", monospace;
      font-size: 9.5pt;
      margin: 8px 0 12px 0;
    }}
    .note {{
      background: #f4f6f9;
      border-left: 4px solid #2e74b5;
      padding: 10px 12px;
      margin: 8px 0 12px 0;
    }}
    .cover {{
      padding: 0 0 12px 0;
      border: none;
      background: transparent;
      border-radius: 0;
      margin-bottom: 18px;
    }}
    .author {{
      font-size: 12pt;
      color: #333;
      margin-top: 10px;
      font-weight: bold;
    }}
    .lede {{
      color: #4d4d4d;
      max-width: 820px;
    }}
    .placeholder {{
      background: #f4f6f9;
      border: 1px dashed #b6c2d0;
      border-radius: 12px;
      padding: 24px 18px;
      margin: 10px 0 16px 0;
      text-align: center;
    }}
    .placeholder-title {{
      font-weight: bold;
      color: #1f4d78;
      margin-bottom: 6px;
    }}
    .placeholder-copy {{
      color: #5a6775;
    }}
  </style>
</head>
<body>
  <div class="cover">
    <h1>VoiceDesk AI</h1>
    <div class="subtitle">Architecture, tools, agent roster, routing logic, and sample prompts</div>
    <div class="author">Author: Ayush Narayan</div>
    <p class="lede">This document summarizes the architecture, the reason each tool is used, the agent roster, routing behavior, and example prompts for the ElevenLabs setup used by this repository.</p>
  </div>

  {section("At a Glance", table(
    ["Area", "Summary"],
    [
      ["Primary user experience", "Live browser-based employee IT support call with multi-agent handoff."],
      ["Demo backend", "FastAPI service that simulates employee verification, incidents, ticketing, and post-call review."],
      ["UI layer", "Streamlit dashboard for scenario control, transcript review, handoff visualization, and structured QA output."],
      ["AI orchestration", "ElevenLabs handles the live voice conversation; Nebius adds optional summarization, routing, review, and escalation drafting."],
    ]
  ))}

  {section("Architecture", """
    <p>The architecture is intentionally split into a live voice front door, a lightweight control plane, and a simulated helpdesk backend. This keeps the demo easy to explain during a presentation while still showing realistic agent specialization and handoff boundaries.</p>
    """ + code_block([
      "Employee caller",
      "      |",
      "      v",
      "ElevenLabs Intake Orchestrator",
      "      |",
      "      +--> Employee Verification  ---> /employees/verify",
      "      +--> IT Resolution Specialist -> /incidents/{category} + runbooks",
      "      +--> IT Escalation Coordinator -> /tickets",
      "      |",
      "      v",
      "Post-call review webhook -> /webhooks/elevenlabs/post-call",
      "      |",
      "      v",
      "Streamlit demo dashboard",
    ]))}

  {section("Tools Used and Why", table(
    ["Tool", "Why it is used", "Where it appears in the repo"],
    [
      ["ElevenLabs Conversational AI", "Live voice interaction layer, turn-taking, and agent handoffs.", "Configured externally; live session URL is loaded from `.env`."],
      ["FastAPI", "Simulated helpdesk backend and webhook receiver for verification, incidents, tickets, and post-call review.", "See `api.py`."],
      ["Streamlit", "Operator-facing demo UI with scenario selection, transcript view, handoff dashboard, and review panel.", "See `app.py`."],
      ["Nebius", "Optional AI support for transcript summarization, routing guidance, QA review, and escalation drafting.", "See `src/nebius_client.py` and `src/service.py`."],
      ["Markdown runbooks", "Small knowledge base for guided troubleshooting and RAG-style resolution support.", "See `runbooks/`."],
      ["ngrok or public deployment", "Makes the local webhook endpoints reachable from ElevenLabs when testing live.", "Used outside the repo when running locally."],
    ]
  ))}

  {section("Agent Roster", table(
    ["Agent", "Primary job", "Key tools", "Handoff rule"],
    [
      ["IT Intake Orchestrator", "Greet the caller, capture the issue, and route only after the problem is stated.", "Conversation flow, optional workflow/procedure, incident lookup.", "Stays in intake until it hears a real issue statement."],
      ["Employee Verification", "Confirm caller identity and basic employee details.", "POST /employees/verify.", "Moves forward only after verification succeeds or a restricted path is chosen."],
      ["IT Resolution Specialist", "Use runbooks to attempt a safe fix.", "GET /incidents/{category}; knowledge base runbooks.", "Escalates if the issue remains unresolved or if a known incident is active."],
      ["IT Escalation Coordinator", "Create a ticket and summarize what was tried.", "POST /tickets.", "Ends the live call after escalation details are confirmed."],
      ["Post-call Review", "Generate structured QA review data.", "POST /webhooks/elevenlabs/post-call.", "Runs after the call, not during the live voice flow."],
    ]
  ))}

  {section("Agent Deep Dive", """
    <h3>IT Intake Orchestrator</h3>
    <p>Purpose: this agent is the live front door. It greets the employee, asks what is wrong, and holds the conversation open until the issue is actually stated.</p>
    <p>Routing logic: do not hand off during the greeting turn. If the caller only says hello or provides identity details, stay in intake and ask one follow-up question. Route to verification or triage only after the issue is explicit.</p>
    """ + code_block([
      "You are the Intake Orchestrator for employee IT support.",
      "",
      "Goals:",
      "- Greet the employee warmly.",
      "- Ask the employee to describe the issue in their own words.",
      "- Do not transfer immediately after the greeting.",
      "- Do not hand off until the employee has clearly stated their issue.",
      "- Ask at most one clarifying question if the issue is still ambiguous.",
      "- Only route to verification or triage after you have enough detail to identify the support path.",
      "- If the caller describes a known incident, route to escalation.",
      "- If the issue appears to be an individual problem, continue through verification and troubleshooting.",
      "",
      "Style:",
      "- Be concise, calm, and professional.",
      "- Do not skip the intake step.",
      "- Do not hand off during the greeting turn.",
      "- Do not infer the problem before the employee speaks.",
    ]) + """
    <h3>Employee Verification</h3>
    <p>Purpose: confirm the caller is the right employee and collect the minimum details needed for support actions.</p>
    <p>Routing logic: if verification succeeds, continue to triage or resolution. If it fails, move to a restricted path and avoid sensitive actions.</p>
    """ + code_block([
      "You are the Verification Agent for employee IT support.",
      "",
      "Goals:",
      "- Confirm the employee's identity using the provided details.",
      "- Ask for one missing field at a time if needed.",
      "- Verify name, employee ID, department, and manager when available.",
      "- If verification fails, keep the caller in a restricted support path.",
      "- If verification succeeds, route to triage or resolution.",
      "- Never resolve issues that require identity verification before confirmation.",
    ]) + """
    <h3>IT Resolution Specialist</h3>
    <p>Purpose: attempt a safe guided fix using the small runbook set in the repository.</p>
    <p>Routing logic: if an active incident exists, do not waste time on local troubleshooting. If the issue is not resolved after the runbook steps, escalate with the attempted steps included.</p>
    """ + code_block([
      "You are the Resolution Specialist for employee IT support.",
      "",
      "Goals:",
      "- Use the knowledge base runbooks to guide troubleshooting.",
      "- Try the simplest safe steps first.",
      "- Limit the session to a small number of clear attempts.",
      "- Summarize what was tried.",
      "- If the issue is resolved, confirm success and end cleanly.",
      "- If the issue is not resolved, escalate with context.",
      "- Do not invent fixes that are not in the runbooks.",
    ]) + """
    <h3>IT Escalation Coordinator</h3>
    <p>Purpose: capture the final summary, create the ticket, and close the live call professionally.</p>
    <p>Routing logic: once a ticket is created and the next support path is clear, do not bounce back to earlier agents unless the demo explicitly needs it.</p>
    """ + code_block([
      "You are the Escalation Coordinator for employee IT support.",
      "",
      "Goals:",
      "- Capture a concise issue summary.",
      "- Capture what was already tried.",
      "- Create a ticket with the right priority.",
      "- State the next support path clearly.",
      "- Reassure the employee about next steps.",
      "- End the live call after escalation details are confirmed.",
    ]) + """
    <h3>Post-call Review</h3>
    <p>Purpose: produce structured QA output after the call ends.</p>
    <p>Routing logic: this is a backend-only step. It consumes the transcript and call state from the webhook and writes a review summary used by the Streamlit dashboard.</p>
    """ + code_block([
      "The review step is not a live voice agent.",
      "It is a webhook-backed backend step that receives the completed call transcript and call state.",
      "It then generates a review record with resolution status, verification status, escalation status, follow-up status, and QA notes.",
    ]))}

  {section("Routing Logic", table(
    ["Step", "Condition", "Next agent", "Notes"],
    [
      ["1", "Caller has not stated the issue yet.", "Stay in intake", "Ask for the issue; do not transfer on greeting alone."],
      ["2", "Issue is stated and identity details are needed.", "Employee Verification", "Collect name, employee ID, department, and manager."],
      ["3", "Issue is an individual problem and no active incident exists.", "IT Resolution Specialist", "Use the runbook and KB."],
      ["4", "Active incident exists or runbook fails.", "IT Escalation Coordinator", "Create ticket and hand off cleanly."],
      ["5", "Call ends.", "Post-call review webhook", "Generate the structured QA record."],
    ]
  ))}

  {section("Visual Placeholders", box("UI Snapshot Placeholder", "Place a screenshot of the Streamlit dashboard here."))}
  {section("Visual Placeholders", box("ElevenLabs Workflow Snapshot Placeholder", "Place a screenshot of the ElevenLabs agent workflow or transfer setup here."))}

  {section("Repository Map", table(
    ["File", "Role"],
    [
      ["app.py", "Streamlit user interface, live status badges, transcript view, handoff dashboard, and review panel."],
      ["api.py", "FastAPI service that receives verification, incident lookup, ticketing, and post-call webhook requests."],
      ["src/service.py", "Call-state engine and deterministic support workflow used by the demo."],
      ["src/scenarios.py", "Scenario definitions used to simulate different employee IT support calls."],
      ["src/nebius_client.py", "Optional Nebius-backed helpers for summarization, routing, review, and escalation drafting."],
      ["runbooks/*.md", "Small support knowledge base used by the resolution agent."],
    ]
  ))}

  {section("What I Learned", """
    <ul>
      <li>A good live voice demo needs narrow agents with explicit handoffs instead of one broad assistant.</li>
      <li>The intake stage must wait for an actual issue statement, not just a greeting or employee name.</li>
      <li>A small helpdesk backend makes the demo feel realistic without adding unnecessary complexity.</li>
      <li>Structured post-call review is helpful because it lets the audience see what happened after the call ended.</li>
      <li>Visual placeholders are useful in a presentation doc because they remind the audience where screenshots and workflow diagrams should go.</li>
      <li>It is easier to explain a multi-agent system when each agent has a single job and a simple routing rule.</li>
    </ul>
  """)}

  {section("Environment Variables", table(
    ["Variable", "Purpose"],
    [
      ["ELEVENLABS_API_KEY", "Enables ElevenLabs connectivity."],
      ["ELEVENLABS_AGENT_ID", "Identifies the live voice agent."],
      ["ELEVENLABS_WEBHOOK_URL", "Public webhook target for post-call or tool callbacks."],
      ["ELEVENLABS_WEB_VOICE_URL", "Live browser session URL for the voice experience."],
      ["NEBIUS_API_KEY", "Optional AI helper access."],
      ["NEBIUS_MODEL", "Model name used by the Nebius client."],
      ["NEBIUS_BASE_URL", "OpenAI-compatible Nebius API base URL."],
    ]
  ))}

  {section("Closing Summary", """
    <p>This project demonstrates a realistic employee IT support workflow where specialized agents collaborate instead of a single general-purpose assistant doing everything. The design keeps the demo approachable for a live presentation while still showing concrete orchestration, tool usage, routing rules, and structured post-call QA.</p>
  """)}
</body>
</html>
"""
    OUT_PATH.write_text(html_doc, encoding="utf-8")
    print(OUT_PATH)


if __name__ == "__main__":
    main()
