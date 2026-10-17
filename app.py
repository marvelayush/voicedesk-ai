from __future__ import annotations

import html
import os
import json

import streamlit as st

from src.local_env import load_local_env
from src.scenarios import SCENARIOS
from src.service import HelpdeskService, CallOrchestrator


load_local_env()


st.set_page_config(
    page_title="VoiceDesk AI",
    page_icon="IT",
    layout="wide",
)


def inject_css() -> None:
    st.markdown(
        """
        <style>
          :root {
            --bg-0: #07111f;
            --bg-1: #0b1629;
            --panel: rgba(10, 19, 35, 0.76);
            --panel-strong: rgba(14, 27, 49, 0.92);
            --line: rgba(149, 190, 255, 0.16);
            --line-strong: rgba(149, 190, 255, 0.28);
            --text: #eef4ff;
            --muted: rgba(238, 244, 255, 0.72);
            --accent: #2a9d8f;
            --accent-2: #f4a261;
            --accent-3: #68c8ff;
          }
          [data-testid="stSidebar"] {
            background:
              radial-gradient(circle at top, rgba(42, 157, 143, 0.12), transparent 35%),
              linear-gradient(180deg, #08111f 0%, #0b182c 100%);
            color: #eef4ff;
            border-right: 1px solid rgba(149, 190, 255, 0.12);
          }
          [data-testid="stSidebar"] * {
            color: #eef4ff !important;
          }
          [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
          [data-testid="stSidebar"] label,
          [data-testid="stSidebar"] span,
          [data-testid="stSidebar"] div {
            color: #eef4ff !important;
          }
          [data-testid="stSidebar"] input,
          [data-testid="stSidebar"] textarea,
          [data-testid="stSidebar"] select {
            background: rgba(255, 255, 255, 0.06) !important;
            color: #eef4ff !important;
            border: 1px solid rgba(149, 190, 255, 0.22) !important;
          }
          [data-testid="stSidebar"] [data-baseweb="select"] {
            background: rgba(255, 255, 255, 0.06) !important;
            border-radius: 10px;
          }
          [data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: rgba(255, 255, 255, 0.06) !important;
            color: #eef4ff !important;
            border-color: rgba(149, 190, 255, 0.22) !important;
          }
          [data-testid="stSidebar"] [data-baseweb="select"] svg {
            fill: #eef4ff !important;
          }
          [data-testid="stSidebar"] [data-baseweb="popover"] {
            background: #0b1629 !important;
            color: #eef4ff !important;
          }
          [data-testid="stSidebar"] [data-baseweb="menu"] {
            background: #0b1629 !important;
            color: #eef4ff !important;
          }
          [data-testid="stSidebar"] [data-baseweb="menu"] ul,
          [data-testid="stSidebar"] [data-baseweb="menu"] li {
            background: #0b1629 !important;
            color: #eef4ff !important;
          }
          [data-testid="stSidebar"] [role="option"] {
            background: #0b1629 !important;
            color: #eef4ff !important;
          }
          [data-testid="stSidebar"] [role="option"]:hover {
            background: rgba(42, 157, 143, 0.2) !important;
          }
          [data-baseweb="popover"] [role="option"],
          [data-baseweb="menu"] [role="option"] {
            background: #0b1629 !important;
            color: #eef4ff !important;
          }
          [data-baseweb="popover"] [role="option"]:hover,
          [data-baseweb="menu"] [role="option"]:hover,
          [data-baseweb="popover"] [role="option"][data-highlighted],
          [data-baseweb="menu"] [role="option"][data-highlighted],
          [data-baseweb="popover"] [role="option"][aria-selected="true"]:hover,
          [data-baseweb="menu"] [role="option"][aria-selected="true"]:hover,
          [data-baseweb="popover"] [role="option"][aria-disabled="false"]:hover,
          [data-baseweb="menu"] [role="option"][aria-disabled="false"]:hover {
            background: rgba(42, 157, 143, 0.22) !important;
            color: #ffffff !important;
          }
          [data-baseweb="popover"] [role="option"][aria-selected="true"],
          [data-baseweb="menu"] [role="option"][aria-selected="true"] {
            background: rgba(104, 200, 255, 0.2) !important;
            color: #ffffff !important;
          }
          [data-baseweb="popover"] [role="option"] *,
          [data-baseweb="menu"] [role="option"] * {
            color: inherit !important;
          }
          [data-testid="stSidebar"] button {
            background: rgba(42, 157, 143, 0.22) !important;
            color: #eef4ff !important;
            border: 1px solid rgba(42, 157, 143, 0.42) !important;
          }
          .stApp {
            background:
              radial-gradient(circle at top left, rgba(42, 157, 143, 0.18), transparent 30%),
              radial-gradient(circle at top right, rgba(244, 162, 97, 0.15), transparent 28%),
              linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 55%, #09111d 100%);
            color: #eef4ff;
          }
          h1, h2, h3, h4 {
            color: var(--text) !important;
            letter-spacing: -0.02em;
          }
          p, label, div, span {
            color: var(--text) !important;
          }
          .block-container {
            padding-top: 2.2rem;
            padding-bottom: 2rem;
          }
          .hero {
            background:
              linear-gradient(135deg, rgba(42, 157, 143, 0.16), rgba(244, 162, 97, 0.08)),
              rgba(10, 19, 35, 0.6);
            border: 1px solid var(--line);
            border-radius: 24px;
            padding: 1.3rem 1.35rem;
            box-shadow: 0 18px 42px rgba(0, 0, 0, 0.22);
            margin-bottom: 1rem;
          }
          .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            font-size: 0.8rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--muted) !important;
          }
          .eyebrow-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-3);
            box-shadow: 0 0 0 4px rgba(104, 200, 255, 0.12);
            display: inline-block;
          }
          .hero-title {
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.05;
            margin-top: 0.35rem;
            margin-bottom: 0.45rem;
          }
          .hero-copy {
            max-width: 900px;
            color: var(--muted) !important;
            font-size: 1rem;
            line-height: 1.6;
          }
          .section-title {
            margin: 1.15rem 0 0.6rem 0;
            font-size: 0.92rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: rgba(238, 244, 255, 0.66) !important;
          }
          .card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 1rem 1.1rem;
            box-shadow: 0 10px 35px rgba(0, 0, 0, 0.25);
          }
          .card-strong {
            background: var(--panel-strong);
            border: 1px solid var(--line-strong);
          }
          .metric {
            font-size: 1.9rem;
            font-weight: 700;
            line-height: 1.0;
          }
          .muted {
            color: rgba(238, 244, 255, 0.68) !important;
            font-size: 0.92rem;
          }
          .agent-pill {
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            background: rgba(42, 157, 143, 0.18);
            border: 1px solid rgba(42, 157, 143, 0.35);
            margin-right: 0.4rem;
            margin-bottom: 0.35rem;
            font-size: 0.82rem;
          }
          .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
            gap: 0.8rem;
          }
          .summary-label {
            color: var(--muted) !important;
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
          }
          .summary-value {
            font-size: 1.15rem;
            font-weight: 700;
            margin-top: 0.18rem;
          }
          .timeline {
            display: flex;
            flex-direction: column;
            gap: 0.65rem;
          }
          .handoff-card {
            display: grid;
            grid-template-columns: 120px 1fr;
            gap: 0.9rem;
            align-items: start;
            background: rgba(12, 22, 41, 0.9);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 0.95rem 1rem;
          }
          .handoff-time {
            color: var(--muted) !important;
            font-size: 0.86rem;
          }
          .handoff-route {
            font-weight: 700;
            margin-bottom: 0.35rem;
          }
          .handoff-reason {
            color: var(--muted) !important;
            line-height: 1.5;
          }
          .handoff-arrow {
            color: var(--accent-3) !important;
            margin: 0 0.25rem;
          }
          .compact-list {
            display: flex;
            flex-direction: column;
            gap: 0.55rem;
          }
          .compact-item {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(149, 190, 255, 0.11);
            border-radius: 14px;
            padding: 0.7rem 0.8rem;
          }
          [data-testid="stButton"] button {
            background: linear-gradient(180deg, #2a9d8f 0%, #1d7e75 100%);
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 12px;
            font-weight: 700;
            padding: 0.65rem 1rem;
            transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
          }
          [data-testid="stButton"] button:hover {
            filter: brightness(1.08);
            transform: translateY(-1px);
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.24);
            color: #ffffff !important;
          }
          [data-testid="stButton"] button:focus,
          [data-testid="stButton"] button:active {
            color: #ffffff !important;
          }
          .call-flow-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.75rem;
            margin-top: 0.85rem;
          }
          .json-box {
            background: #07111f;
            border: 1px solid rgba(149, 190, 255, 0.18);
            border-radius: 16px;
            padding: 1rem 1.05rem;
            color: #dbe8ff;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-word;
            font-size: 0.88rem;
            line-height: 1.55;
          }
          .speaker-chip {
            display: inline-block;
            padding: 0.1rem 0.55rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            margin-right: 0.45rem;
            border: 1px solid rgba(255, 255, 255, 0.14);
          }
          .speaker-caller { background: rgba(104, 200, 255, 0.18); color: #9fdcff; }
          .speaker-system { background: rgba(238, 244, 255, 0.08); color: rgba(238, 244, 255, 0.7); }
          .speaker-intake_agent { background: rgba(42, 157, 143, 0.22); color: #7fe0d3; }
          .speaker-verification_agent { background: rgba(155, 120, 255, 0.2); color: #c7b6ff; }
          .speaker-triage_agent { background: rgba(244, 162, 97, 0.2); color: #ffc79a; }
          .speaker-resolution_agent { background: rgba(30, 160, 120, 0.22); color: #8ff0c4; }
          .speaker-escalation_agent { background: rgba(231, 111, 81, 0.22); color: #ffab96; }
          .source-badge {
            display: inline-block;
            margin-left: 0.4rem;
            padding: 0.05rem 0.45rem;
            border-radius: 6px;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            background: rgba(149, 190, 255, 0.14);
            color: rgba(238, 244, 255, 0.75);
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def esc(value: object) -> str:
    """Escape anything that came from a caller, webhook, or LLM before it reaches unsafe HTML."""
    return html.escape(str(value), quote=True)


def label(value: str) -> str:
    return esc(str(value).replace("_", " ").title())


def source_badge(source: str) -> str:
    return f'<span class="source-badge">{esc(source)}</span>' if source else ""


def init_state() -> None:
    if "service" not in st.session_state:
        st.session_state.service = HelpdeskService()
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = CallOrchestrator(st.session_state.service)
    if "call_state" not in st.session_state:
        st.session_state.call_state = None
    if "selected_scenario_id" not in st.session_state:
        st.session_state.selected_scenario_id = SCENARIOS[0].id
    if "call_history" not in st.session_state:
        st.session_state.call_history = []


def record_call_history(call_state) -> None:
    review = getattr(call_state, "review", None)
    if not review:
        return
    history = st.session_state.call_history
    if any(item["call_id"] == review["call_id"] for item in history):
        return
    scenario = next((s for s in SCENARIOS if s.id == call_state.scenario_id), None)
    if review.get("resolved"):
        outcome = "Resolved"
    elif review.get("identity_hold"):
        outcome = "Identity hold"
    else:
        outcome = "Escalated"
    history.append(
        {
            "call_id": review["call_id"],
            "scenario": scenario.title if scenario else call_state.scenario_id,
            "issue": review.get("issue_category", "-"),
            "outcome": outcome,
            "ticket": review.get("ticket_id") or "-",
            "handoffs": review.get("handoff_count", 0),
            "process_ok": bool(review.get("correct_process_followed")),
        }
    )


def get_elevenlabs_live_url() -> str:
    return (
        os.getenv("ELEVENLABS_WEB_VOICE_URL", "").strip()
        or os.getenv("ELEVENLABS_LIVE_URL", "").strip()
    )


def render_header() -> None:
    elevenlabs_ready = bool(os.getenv("ELEVENLABS_API_KEY", "").strip())
    nebius_ready = bool(os.getenv("NEBIUS_API_KEY", "").strip())
    live_voice_ready = bool(get_elevenlabs_live_url())

    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow"><span class="eyebrow-dot"></span> Multi-agent support workflow</div>
          <div class="hero-title">Employee IT support, orchestrated by specialized agents.</div>
          <div class="hero-copy">
            This demo simulates an employee calling IT support. ElevenLabs handles the live voice conversation,
            while this app shows the handoffs, backend actions, and post-call review in a polished product-style view.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="display:flex; gap:0.55rem; flex-wrap:wrap; margin-top:-0.15rem; margin-bottom:0.95rem;">
          <span class="agent-pill" style="background:{'rgba(30, 160, 120, 0.24)' if elevenlabs_ready else 'rgba(244, 162, 97, 0.18)'}; border-color:{'rgba(30, 160, 120, 0.5)' if elevenlabs_ready else 'rgba(244, 162, 97, 0.35)'};">
            ElevenLabs: {'Connected' if elevenlabs_ready else 'Not configured'}
          </span>
          <span class="agent-pill" style="background:{'rgba(30, 160, 120, 0.24)' if live_voice_ready else 'rgba(244, 162, 97, 0.18)'}; border-color:{'rgba(30, 160, 120, 0.5)' if live_voice_ready else 'rgba(244, 162, 97, 0.35)'};">
            Live voice: {'Ready' if live_voice_ready else 'Not configured'}
          </span>
          <span class="agent-pill" style="background:{'rgba(30, 160, 120, 0.24)' if nebius_ready else 'rgba(244, 162, 97, 0.18)'}; border-color:{'rgba(30, 160, 120, 0.5)' if nebius_ready else 'rgba(244, 162, 97, 0.35)'};">
            Nebius: {'Connected' if nebius_ready else 'Not configured'}
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview() -> None:
    st.markdown(
        """
        <div class="card card-strong">
          <div class="muted">How the demo works</div>
          <div style="margin-top:0.45rem; line-height:1.55;">
            Start a scripted call to watch the issue move through intake, verification, triage, resolution, and escalation.
            The transcript on the left shows what the caller and agents said.
            The panel on the right shows which agent is active and why the handoff happened.
            The review section at the bottom summarizes whether the issue was handled correctly.
          </div>
          <div class="call-flow-grid">
            <span class="agent-pill">1. Intake</span>
            <span class="agent-pill">2. Verify employee</span>
            <span class="agent-pill">3. Triage issue</span>
            <span class="agent-pill">4. Resolve or escalate</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    st.sidebar.markdown("## Demo Controls")
    st.sidebar.markdown(
        "<div style='color: rgba(238,244,255,0.72); line-height:1.5; margin-bottom:0.5rem;'>Choose a scenario and run the scripted flow.</div>",
        unsafe_allow_html=True,
    )
    scenario_labels = {s.id: f"{s.title}" for s in SCENARIOS}
    scenario_id = st.sidebar.selectbox(
        "Scenario",
        options=list(scenario_labels.keys()),
        format_func=lambda key: scenario_labels[key],
        index=list(scenario_labels.keys()).index(st.session_state.selected_scenario_id),
    )
    st.session_state.selected_scenario_id = scenario_id

    agent_id = os.getenv("ELEVENLABS_AGENT_ID", "").strip()
    webhook_url = os.getenv("ELEVENLABS_WEBHOOK_URL", "").strip()
    live_url = get_elevenlabs_live_url()
    api_key_set = bool(os.getenv("ELEVENLABS_API_KEY", "").strip())

    st.sidebar.markdown("### ElevenLabs")
    st.sidebar.markdown(
        f"""
        <div class="card">
          <div class="muted">Configured from environment</div>
          <div style="margin-top:0.35rem;line-height:1.55;">
            <div><strong>Agent ID:</strong> {agent_id or "not set"}</div>
            <div><strong>API Key:</strong> {"set" if api_key_set else "not set"}</div>
            <div><strong>Live Voice URL:</strong> {live_url or "not set"}</div>
            <div><strong>Webhook URL:</strong> {webhook_url or "not set"}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        "<div style='color: rgba(238,244,255,0.72); line-height:1.45; margin-top:0.4rem;'>Set these values in your environment or `.env` file. If they are empty, the demo stays in simulated mode.</div>",
        unsafe_allow_html=True,
    )


def render_live_voice_panel() -> None:
    live_url = get_elevenlabs_live_url()
    st.subheader("Live Voice Panel")
    if not live_url:
        st.markdown(
            """
            <div class="card card-strong">
              <div class="muted">Live panel not configured yet</div>
              <div style="margin-top:0.35rem;line-height:1.6;">
                Set <strong>ELEVENLABS_WEB_VOICE_URL</strong> in your <code>.env</code> file to embed the ElevenLabs session here.
                If the live page refuses to frame, the same URL can still be opened directly from the browser.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    safe_url = html.escape(live_url, quote=True)
    st.markdown(
        f"""
        <div class="card card-strong">
          <div class="muted">Open the live browser voice session</div>
          <div style="margin-top:0.35rem;line-height:1.55;">
            ElevenLabs blocks iframe embedding for this page, so the live voice experience has to be opened directly.
            Use the link below to launch the intake orchestrator in a separate tab.
          </div>
          <div style="margin-top:0.45rem;line-height:1.55;color:rgba(238,244,255,0.82);">
            The intake agent should wait for the caller to describe the issue before routing. If it transfers on the greeting alone, the routing rule is too broad.
          </div>
          <div style="margin-top:0.6rem;">
            <a href="{safe_url}" target="_blank" rel="noreferrer" style="color:#68c8ff;font-weight:700;text-decoration:none;">
              Open live session in a new tab
            </a>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="card" style="margin-top:0.8rem;">
          <div class="muted">Why the embed failed</div>
          <div style="margin-top:0.35rem;line-height:1.55;">
            The ElevenLabs page sends browser security headers that prevent it from being framed inside Streamlit.
            The demo still works, but the session must run in its own tab.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_start_card() -> None:
    scenario = next(s for s in SCENARIOS if s.id == st.session_state.selected_scenario_id)
    with st.container():
        st.markdown(
            f"""
            <div class="card card-strong">
              <div class="muted">Selected scenario</div>
              <div style="font-size:1.35rem;font-weight:700;margin-top:0.15rem;">{esc(scenario.title)}</div>
              <div style="margin-top:0.4rem;line-height:1.5;">{esc(scenario.summary)}</div>
              <div style="margin-top:0.8rem;">
                <span class="agent-pill">Issue: {esc(scenario.category)}</span>
                <span class="agent-pill">Target: {esc(scenario.expected_outcome)}</span>
                <span class="agent-pill">Demo path: {esc(scenario.demo_path)}</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("Start call flow", width="stretch"):
            st.session_state.call_state = st.session_state.orchestrator.start_call(scenario)
    with c2:
        if st.button("Advance one step", width="stretch", disabled=st.session_state.call_state is None):
            st.session_state.call_state = st.session_state.orchestrator.advance(st.session_state.call_state)
    with c3:
        if st.button("Run full demo", width="stretch"):
            current = st.session_state.call_state
            if current is None or current.scenario_id != scenario.id or current.phase == "review":
                st.session_state.call_state = st.session_state.orchestrator.start_call(scenario)
            for _ in range(10):
                current = st.session_state.call_state
                if current is None or current.phase in ("review", "done"):
                    break
                st.session_state.call_state = st.session_state.orchestrator.advance(current)
        if st.button("Reset all", width="stretch"):
            st.session_state.call_state = None


def render_status_row(call_state) -> None:
    cols = st.columns(4)
    metrics = [
        ("Active Agent", getattr(call_state, "active_agent", "Idle").replace("_", " ").title() if call_state else "Idle"),
        ("Resolved", "Yes" if getattr(call_state, "resolved", False) else "No"),
        ("Escalated", "Yes" if getattr(call_state, "escalated", False) else "No"),
        ("Phase", getattr(call_state, "phase", "Not started").replace("_", " ").title() if call_state else "Not started"),
    ]
    for col, (metric_label, value) in zip(cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class="card card-strong">
                  <div class="muted">{metric_label}</div>
                  <div class="metric">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_transcript(call_state) -> None:
    st.subheader("Live Transcript")
    if not call_state:
        st.info("Start a call to see the live transcript and handoffs.")
        return

    for entry in getattr(call_state, "transcript", []):
        speaker = str(entry["speaker"])
        speaker_class = speaker if speaker.replace("_", "").isalnum() else "system"
        st.markdown(
            f"""
            <div class="card" style="margin-bottom:0.6rem;">
              <div class="muted"><span class="speaker-chip speaker-{speaker_class}">{label(speaker)}</span>{esc(entry["timestamp"])}</div>
              <div style="margin-top:0.35rem;">{esc(entry["text"])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_handoff_dashboard(call_state) -> None:
    st.subheader("Handoff Dashboard")
    if not call_state:
        st.info("No active handoff yet.")
        return
    handoffs = getattr(call_state, "handoffs", [])
    if not handoffs:
        st.markdown(
            """
            <div class="card">
              <div class="muted">No handoffs yet</div>
              <div style="margin-top:0.35rem;">The call will show a route once intake starts passing work to specialist agents.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown('<div class="timeline">', unsafe_allow_html=True)
    for item in handoffs:
        st.markdown(
            f"""
            <div class="handoff-card">
              <div>
                <div class="handoff-time">{esc(item['timestamp'])}</div>
              </div>
              <div>
                <div class="handoff-route">{label(item['from'])} <span class="handoff-arrow">→</span> {label(item['to'])}</div>
                <div class="handoff-reason">{esc(item['reason'])}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_ai_insights(call_state) -> None:
    st.subheader("AI Insights")
    st.caption("Generated by Nebius when configured; otherwise by the deterministic rules engine. The badge shows which one.")
    if not call_state:
        st.info("Route suggestions, escalation drafts, and review summaries appear once a call runs.")
        return
    route_suggestion = getattr(call_state, "route_suggestion", "")
    escalation_draft = getattr(call_state, "escalation_draft", "")
    review = getattr(call_state, "review", None) or {}
    review_summary = review.get("summary", "")

    cols = st.columns(3)
    with cols[0]:
        st.markdown(
            f"""
            <div class="card card-strong">
              <div class="muted">Route Suggestion{source_badge(getattr(call_state, "route_source", ""))}</div>
              <div class="metric">{label(route_suggestion) if route_suggestion else "Pending"}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            f"""
            <div class="card card-strong">
              <div class="muted">Escalation Draft{source_badge(getattr(call_state, "escalation_source", ""))}</div>
              <div style="margin-top:0.35rem;line-height:1.55;">{esc(escalation_draft) if escalation_draft else "No escalation draft yet."}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            f"""
            <div class="card card-strong">
              <div class="muted">Transcript Summary{source_badge(review.get("summary_source", ""))}</div>
              <div style="margin-top:0.35rem;line-height:1.55;white-space:pre-wrap;">{esc(review_summary) if review_summary else "Summary appears after review."}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_review_panel(call_state) -> None:
    st.subheader("Post-Call Review")
    review = getattr(call_state, "review", {}) if call_state else {}
    if not call_state or not review:
        st.markdown(
            """
            <div class="card card-strong">
              <div class="muted">Review pending</div>
              <div style="margin-top:0.35rem;line-height:1.6;">
                Once the call reaches the review step, this area will show whether the issue was resolved,
                whether the employee was verified, and whether follow-up is required.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    cols = st.columns(4)
    review_metrics = [
        ("Resolved", "Yes" if review.get("resolved") else "No"),
        ("Verified", "Yes" if review.get("employee_verified") else "No"),
        ("Escalated", "Yes" if review.get("escalated") else "No"),
        ("Follow-up", "Yes" if review.get("follow_up_required") else "No"),
    ]
    for col, (metric_label, value) in zip(cols, review_metrics):
        with col:
            st.markdown(
                f"""
                <div class="card card-strong">
                  <div class="muted">{metric_label}</div>
                  <div class="metric">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        f"""
        <div class="card card-strong" style="margin-top:0.8rem;">
          <div class="muted">Review Summary</div>
          <div style="margin-top:0.35rem;font-size:1.05rem;line-height:1.6;white-space:pre-wrap;">{esc(review.get('summary', ''))}</div>
          <div style="margin-top:0.6rem;color:rgba(238,244,255,0.72);line-height:1.5;">{esc(' '.join(review.get('qa_notes', [])) or 'No QA notes.')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**Structured review data**")
    st.markdown(
        """
        <div class="summary-grid">
        """,
        unsafe_allow_html=True,
    )
    structured_fields = [
        ("Call ID", review.get("call_id", "-")),
        ("Issue", review.get("issue_category", "-")),
        ("Ticket", review.get("ticket_id") or "None"),
        ("Turns", str(review.get("transcript_turns", 0))),
        ("Handoffs", str(review.get("handoff_count", 0))),
        ("Agents", ", ".join(a.replace("_agent", "") for a in review.get("agents_involved", [])) or "-"),
        ("Process", "Followed" if review.get("correct_process_followed") else "Needs review"),
        ("Generated", review.get("generated_at", "-")),
    ]
    for field_label, value in structured_fields:
        st.markdown(
            f"""
            <div class="compact-item">
              <div class="summary-label">{field_label}</div>
              <div class="summary-value">{esc(value)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "Download review (JSON)",
            data=json.dumps(review, indent=2, sort_keys=True),
            file_name=f"{review.get('call_id', 'call')}_review.json",
            mime="application/json",
            width="stretch",
        )
    with d2:
        st.download_button(
            "Download transcript (JSON)",
            data=json.dumps(call_state.transcript, indent=2),
            file_name=f"{review.get('call_id', 'call')}_transcript.json",
            mime="application/json",
            width="stretch",
        )

    with st.expander("Show raw structured JSON"):
        st.markdown(
            f"""
            <pre class="json-box">{html.escape(json.dumps(review, indent=2, sort_keys=True))}</pre>
            """,
            unsafe_allow_html=True,
        )


def render_backend_panel(service: HelpdeskService) -> None:
    st.subheader("Simulated Helpdesk")
    cols = st.columns(3)
    with cols[0]:
        st.markdown("**Directory**")
        st.markdown('<div class="compact-list">', unsafe_allow_html=True)
        for employee_id, record in service.directory_summary().items():
            st.markdown(
                f"""
                <div class="compact-item">
                  <div style="font-weight:700;">{record['name']}</div>
                  <div class="muted">{employee_id} - {record['department']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown("**Active incidents**")
        st.markdown('<div class="compact-list">', unsafe_allow_html=True)
        for category, incident in service.incident_summary().items():
            state = "Active" if incident["active"] else "Clear"
            st.markdown(
                f"""
                <div class="compact-item">
                  <div style="font-weight:700;">{category.replace('_', ' ').title()}</div>
                  <div class="muted">{state} - {incident['summary']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[2]:
        st.markdown("**Tickets**")
        tickets = service.ticket_summary()
        if not tickets:
            st.markdown(
                """
                <div class="compact-item">
                  <div style="font-weight:700;">No tickets yet</div>
                  <div class="muted">Run an escalated scenario to create one.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="compact-list">', unsafe_allow_html=True)
            for ticket in tickets:
                st.markdown(
                    f"""
                    <div class="compact-item">
                      <div style="font-weight:700;">{esc(ticket['ticket_id'])} - {label(ticket['category'])}</div>
                      <div class="muted">{esc(ticket['priority'])} priority - {esc(ticket['status'])} - {esc(ticket['summary'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)


def render_call_history() -> None:
    st.subheader("Session Call History")
    history = st.session_state.call_history
    if not history:
        st.info("Completed calls from this session will be listed here.")
        return
    total = len(history)
    resolved = sum(1 for item in history if item["outcome"] == "Resolved")
    process_ok = sum(1 for item in history if item["process_ok"])
    cols = st.columns(3)
    for col, (metric_label, value) in zip(
        cols,
        [
            ("Calls completed", str(total)),
            ("Resolved on call", f"{resolved / total:.0%}"),
            ("Correct process", f"{process_ok / total:.0%}"),
        ],
    ):
        with col:
            st.markdown(
                f"""
                <div class="card card-strong">
                  <div class="muted">{metric_label}</div>
                  <div class="metric">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.dataframe(history, width="stretch", hide_index=True)


def render_integration_notes() -> None:
    st.subheader("ElevenLabs Integration Notes")
    st.markdown(
        """
        - Use the FastAPI endpoints in `api.py` as webhook tools.
        - Upload the Markdown files in `runbooks/` into the ElevenLabs knowledge base.
        - Enable RAG on the voice agent so resolution can cite those runbooks.
        - Use agent transfer for escalation handoff.
        - Use the post-call webhook to send transcript and state into the review pipeline.
        """
    )


inject_css()
init_state()
render_header()
render_overview()
render_sidebar()
render_start_card()
render_live_voice_panel()

call_state = st.session_state.call_state
if call_state:
    call_state = st.session_state.orchestrator.sync_review_if_needed(call_state)
    st.session_state.call_state = call_state
    record_call_history(call_state)

render_status_row(call_state)

left, right = st.columns([1.2, 1])
with left:
    render_transcript(call_state)
with right:
    render_handoff_dashboard(call_state)

st.divider()
render_ai_insights(call_state)

st.divider()
render_review_panel(call_state)

st.divider()
render_backend_panel(st.session_state.service)

st.divider()
render_call_history()

st.divider()
render_integration_notes()

if call_state and call_state.phase == "review":
    st.success("Call completed. The QA review has been generated.")
