from __future__ import annotations

from pathlib import Path


OUT_PATH = Path("docs") / "multi_agent_it_support_voice_demo_documentation.rtf"


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rtf = r"""{\rtf1\ansi\deff0
{\fonttbl{\f0 Arial;}{\f1 Courier New;}}
{\colortbl ;\red0\green0\blue0;\red46\green116\blue181;\red31\green77\blue120;\red102\green102\blue102;\red244\green246\blue249;\red232\green238\blue245;\red198\green207\blue219;}
\paperw12240\paperh15840\margl1440\margr1440\margt1440\margb1440
\qc
\fs56\b VoiceDesk AI\par
\fs24\b0\cf4 Architecture, tools, agents, routing, and sample prompts\par
\fs22\cf0\par
\fs24 Author: Ayush Narayan\par
\fs20 Prepared for the live ElevenLabs voice demo\par
\fs20\par
\fs20 This document explains how the system is structured, why each tool exists, how the agents hand off work, and what was learned while building the demo.\par
\fs20\par
\page
\ql
\fs28\b Overview\par
\fs22\b0 The demo presents employee IT support as a multi-agent voice workflow. ElevenLabs handles the live conversation, FastAPI simulates the helpdesk systems, Streamlit presents the control room, and Nebius optionally supports review and routing tasks.\par
\par
\fs24\b At a Glance\par
\fs22\b0
\trowd\trgaph108\trleft0\cellx2500\cellx9360
\clcbpat6\intbl\b Area\b0\cell\clcbpat6\intbl\b Summary\b0\cell\row
\trowd\trgaph108\trleft0\cellx2500\cellx9360
\intbl Primary user experience\cell\intbl Live browser-based employee IT support call with multi-agent handoff.\cell\row
\trowd\trgaph108\trleft0\cellx2500\cellx9360
\intbl Demo backend\cell\intbl FastAPI service that simulates employee verification, incidents, ticketing, and post-call review.\cell\row
\trowd\trgaph108\trleft0\cellx2500\cellx9360
\intbl UI layer\cell\intbl Streamlit dashboard for scenario control, transcript review, handoff visualization, and structured QA output.\cell\row
\trowd\trgaph108\trleft0\cellx2500\cellx9360
\intbl AI orchestration\cell\intbl ElevenLabs handles the live voice conversation; Nebius adds optional summarization, routing, review, and escalation drafting.\cell\row
\par
\fs28\b Architecture\par
\fs22\b0 The architecture is intentionally split into a live voice front door, a lightweight control plane, and a simulated helpdesk backend. This keeps the demo easy to explain while still showing realistic agent specialization and handoff boundaries.\par
\f1\fs18 Employee caller\par      |\par      v\par ElevenLabs Intake Orchestrator\par      |\par      +--> Employee Verification  ---> /employees/verify\par      +--> IT Resolution Specialist -> /incidents/{category} + runbooks\par      +--> IT Escalation Coordinator -> /tickets\par      |\par      v\par Post-call review webhook -> /webhooks/elevenlabs/post-call\par      |\par      v\par Streamlit demo dashboard\par\f0
\par
\fs24\b Tooling Choices\par
\fs22\b0
\trowd\trgaph108\trleft0\cellx2200\cellx7000\cellx9360
\clcbpat6\intbl\b Tool\b0\cell\clcbpat6\intbl\b Why it is used\b0\cell\clcbpat6\intbl\b Where it appears in the repo\b0\cell\row
\trowd\trgaph108\trleft0\cellx2200\cellx7000\cellx9360
\intbl ElevenLabs Conversational AI\cell\intbl Live voice interaction layer, turn-taking, and agent handoffs.\cell\intbl Configured externally; live session URL is loaded from .env.\cell\row
\trowd\trgaph108\trleft0\cellx2200\cellx7000\cellx9360
\intbl FastAPI\cell\intbl Simulated helpdesk backend and webhook receiver for verification, incidents, tickets, and post-call review.\cell\intbl api.py\cell\row
\trowd\trgaph108\trleft0\cellx2200\cellx7000\cellx9360
\intbl Streamlit\cell\intbl Operator-facing demo UI with scenario selection, transcript view, handoff dashboard, and review panel.\cell\intbl app.py\cell\row
\trowd\trgaph108\trleft0\cellx2200\cellx7000\cellx9360
\intbl Nebius\cell\intbl Optional AI support for transcript summarization, routing guidance, QA review, and escalation drafting.\cell\intbl src/nebius_client.py and src/service.py\cell\row
\trowd\trgaph108\trleft0\cellx2200\cellx7000\cellx9360
\intbl Markdown runbooks\cell\intbl Small knowledge base for guided troubleshooting and RAG-style resolution support.\cell\intbl runbooks/\cell\row
\trowd\trgaph108\trleft0\cellx2200\cellx7000\cellx9360
\intbl ngrok or public deployment\cell\intbl Makes the local webhook endpoints reachable from ElevenLabs when testing live.\cell\intbl Used outside the repo when running locally.\cell\row
\par
\fs24\b Agent Roster\par
\fs22\b0
\trowd\trgaph108\trleft0\cellx2200\cellx4400\cellx7000\cellx9360
\clcbpat6\intbl\b Agent\b0\cell\clcbpat6\intbl\b Primary job\b0\cell\clcbpat6\intbl\b Key tools\b0\cell\clcbpat6\intbl\b Handoff rule\b0\cell\row
\trowd\trgaph108\trleft0\cellx2200\cellx4400\cellx7000\cellx9360
\intbl IT Intake Orchestrator\cell\intbl Greet the caller, capture the issue, and route only after the problem is stated.\cell\intbl Conversation flow, optional workflow/procedure, incident lookup.\cell\intbl Stays in intake until it hears a real issue statement.\cell\row
\trowd\trgaph108\trleft0\cellx2200\cellx4400\cellx7000\cellx9360
\intbl Employee Verification\cell\intbl Confirm caller identity and basic employee details.\cell\intbl POST /employees/verify.\cell\intbl Moves forward only after verification succeeds or a restricted path is chosen.\cell\row
\trowd\trgaph108\trleft0\cellx2200\cellx4400\cellx7000\cellx9360
\intbl IT Resolution Specialist\cell\intbl Use runbooks to attempt a safe fix.\cell\intbl GET /incidents/{category}; knowledge base runbooks.\cell\intbl Escalates if the issue remains unresolved or if a known incident is active.\cell\row
\trowd\trgaph108\trleft0\cellx2200\cellx4400\cellx7000\cellx9360
\intbl IT Escalation Coordinator\cell\intbl Create a ticket and summarize what was tried.\cell\intbl POST /tickets.\cell\intbl Ends the live call after escalation details are confirmed.\cell\row
\trowd\trgaph108\trleft0\cellx2200\cellx4400\cellx7000\cellx9360
\intbl Post-call Review\cell\intbl Generate structured QA review data.\cell\intbl POST /webhooks/elevenlabs/post-call.\cell\intbl Runs after the call, not during the live voice flow.\cell\row
\par
\fs24\b Routing Logic\par
\fs22\b0
1. Caller has not stated the issue yet: stay in intake and ask for the issue; do not transfer on greeting alone.\par
2. Issue is stated and identity details are needed: move to Employee Verification.\par
3. Issue is an individual problem and no active incident exists: move to IT Resolution Specialist.\par
4. Active incident exists or runbook fails: move to IT Escalation Coordinator.\par
5. Call ends: trigger the post-call review webhook.\par
\par
\fs24\b Visual Placeholders\par
\fs22\b0
\trowd\trgaph108\trleft0\cellx9360
\clcbpat5\intbl\qc\b UI Snapshot Placeholder\par\b0 Place a screenshot of the Streamlit dashboard here.\cell\row
\par
\trowd\trgaph108\trleft0\cellx9360
\clcbpat5\intbl\qc\b ElevenLabs Workflow Snapshot Placeholder\par\b0 Place a screenshot of the ElevenLabs agent workflow or transfer setup here.\cell\row
\par
\fs24\b Sample Prompts\par
\fs22\b0
\fs22\b IT Intake Orchestrator\par\b0
\f1\fs18 You are the Intake Orchestrator for employee IT support.\par
\par
Goals:\par
- Greet the employee warmly.\par
- Ask the employee to describe the issue in their own words.\par
- Do not transfer immediately after the greeting.\par
- Do not hand off until the employee has clearly stated their issue.\par
- Ask at most one clarifying question if the issue is still ambiguous.\par
- Only route to verification or triage after you have enough detail to identify the support path.\par
- If the caller describes a known incident, route to escalation.\par
- If the issue appears to be an individual problem, continue through verification and troubleshooting.\par
- If the employee has not stated a problem yet, stay in intake and continue the conversation.\par
- Do not make a routing decision based only on the greeting.\par
- Do not infer the issue from the employee identity alone.\par
- Wait for an explicit problem statement before any handoff.\par
\par
Style:\par
- Be concise, calm, and professional.\par
- Do not skip the intake step.\par
- Do not hand off during the greeting turn.\par
- Do not infer the problem before the employee speaks.\par\f0
\par
\fs22\b Employee Verification\par\b0
\f1\fs18 You are the Verification Agent for employee IT support.\par
\par
Goals:\par
- Confirm the employee's identity using the provided details.\par
- Ask for one missing field at a time if needed.\par
- Verify name, employee ID, department, and manager when available.\par
- If verification fails, keep the caller in a restricted support path.\par
- If verification succeeds, route to triage or resolution.\par
- Never resolve issues that require identity verification before confirmation.\par\f0
\par
\fs22\b IT Escalation Coordinator\par\b0
\f1\fs18 You are the Escalation Coordinator for employee IT support.\par
\par
Goals:\par
- Capture a concise issue summary.\par
- Capture what was already tried.\par
- Create a ticket with the right priority.\par
- State the next support path clearly.\par
- Reassure the employee about next steps.\par
- End the live call after escalation details are confirmed.\par\f0
\par
\fs24\b What I Learned\par
\fs22\b0
- A good live voice demo needs narrow agents with explicit handoffs instead of one broad assistant.\par
- The intake stage must wait for an actual issue statement, not just a greeting or employee name.\par
- A small helpdesk backend makes the demo feel realistic without adding unnecessary complexity.\par
- Structured post-call review is helpful because it lets the audience see what happened after the call ended.\par
- Visual placeholders are useful in a presentation doc because they remind the audience where screenshots and workflow diagrams should go.\par
- It is easier to explain a multi-agent system when each agent has a single job and a simple routing rule.\par
\par
\fs24\b Repository Map\par
\fs22\b0 app.py - Streamlit UI\par
api.py - FastAPI service\par
src/service.py - call-state engine\par
src/scenarios.py - scenario data\par
src/nebius_client.py - optional AI helpers\par
runbooks/*.md - troubleshooting knowledge base\par
\par
\fs24\b Environment Variables\par
\fs22\b0 ELEVENLABS_API_KEY, ELEVENLABS_AGENT_ID, ELEVENLABS_WEBHOOK_URL, ELEVENLABS_WEB_VOICE_URL, NEBIUS_API_KEY, NEBIUS_MODEL, NEBIUS_BASE_URL\par
}
"""
    OUT_PATH.write_text(rtf, encoding="ascii")
    print(OUT_PATH)


if __name__ == "__main__":
    main()
