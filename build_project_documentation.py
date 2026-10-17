from __future__ import annotations

import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET


OUT_PATH = Path("docs") / "multi_agent_it_support_voice_demo_documentation.docx"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "dcmitype": "http://purl.org/dc/dcmitype/",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


def qn(prefix: str, tag: str) -> str:
    return f"{{{NS[prefix]}}}{tag}"


def pt_to_half_points(pt: float) -> str:
    return str(int(round(pt * 2)))


def color_hex(hex_value: str) -> str:
    return hex_value.replace("#", "").upper()


def make_run(
    text: str,
    *,
    bold: bool = False,
    italic: bool = False,
    font: str = "Calibri",
    size_pt: float = 11,
    color: str = "000000",
    monospace: bool = False,
) -> ET.Element:
    r = ET.Element(qn("w", "r"))
    rPr = ET.SubElement(r, qn("w", "rPr"))
    if bold:
        ET.SubElement(rPr, qn("w", "b"))
    if italic:
        ET.SubElement(rPr, qn("w", "i"))
    fonts = ET.SubElement(rPr, qn("w", "rFonts"))
    font_name = "Courier New" if monospace else font
    fonts.set(qn("w", "ascii"), font_name)
    fonts.set(qn("w", "hAnsi"), font_name)
    fonts.set(qn("w", "cs"), font_name)
    size = pt_to_half_points(size_pt)
    ET.SubElement(rPr, qn("w", "sz")).set(qn("w", "val"), size)
    ET.SubElement(rPr, qn("w", "szCs")).set(qn("w", "val"), size)
    ET.SubElement(rPr, qn("w", "color")).set(qn("w", "val"), color_hex(color))
    t = ET.SubElement(r, qn("w", "t"))
    if text.startswith(" ") or text.endswith(" "):
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text
    return r


def make_paragraph(
    text: str = "",
    *,
    bold: bool = False,
    italic: bool = False,
    font: str = "Calibri",
    size_pt: float = 11,
    color: str = "000000",
    monospace: bool = False,
    align: str | None = None,
    before_pt: float = 0,
    after_pt: float = 6,
    line_pt: float = 14,
    left_twips: int = 0,
    right_twips: int = 0,
    first_line_twips: int = 0,
    shading: str | None = None,
) -> ET.Element:
    p = ET.Element(qn("w", "p"))
    pPr = ET.SubElement(p, qn("w", "pPr"))
    spacing = ET.SubElement(pPr, qn("w", "spacing"))
    spacing.set(qn("w", "before"), str(int(round(before_pt * 20))))
    spacing.set(qn("w", "after"), str(int(round(after_pt * 20))))
    spacing.set(qn("w", "line"), str(int(round(line_pt * 20))))
    spacing.set(qn("w", "lineRule"), "auto")
    if align:
        ET.SubElement(pPr, qn("w", "jc")).set(qn("w", "val"), align)
    if left_twips or right_twips or first_line_twips:
        ind = ET.SubElement(pPr, qn("w", "ind"))
        if left_twips:
            ind.set(qn("w", "left"), str(left_twips))
        if right_twips:
            ind.set(qn("w", "right"), str(right_twips))
        if first_line_twips:
            ind.set(qn("w", "firstLine"), str(first_line_twips))
    if shading:
        shd = ET.SubElement(pPr, qn("w", "shd"))
        shd.set(qn("w", "val"), "clear")
        shd.set(qn("w", "color"), "auto")
        shd.set(qn("w", "fill"), color_hex(shading))
    if text:
        p.append(make_run(text, bold=bold, italic=italic, font=font, size_pt=size_pt, color=color, monospace=monospace))
    return p


def add_title_paragraph(body: ET.Element, text: str) -> None:
    body.append(
        make_paragraph(
            text,
            bold=True,
            font="Calibri",
            size_pt=24,
            color="1F1F1F",
            align="left",
            before_pt=0,
            after_pt=2,
            line_pt=24,
        )
    )


def add_subtitle(body: ET.Element, text: str) -> None:
    body.append(
        make_paragraph(
            text,
            font="Calibri",
            size_pt=11,
            color="666666",
            after_pt=10,
            line_pt=13,
        )
    )


def add_heading(body: ET.Element, text: str, level: int) -> None:
    if level == 1:
        body.append(
            make_paragraph(
                text,
                bold=True,
                font="Calibri",
                size_pt=16,
                color="2E74B5",
                before_pt=16,
                after_pt=6,
                line_pt=18,
            )
        )
    elif level == 2:
        body.append(
            make_paragraph(
                text,
                bold=True,
                font="Calibri",
                size_pt=13,
                color="2E74B5",
                before_pt=12,
                after_pt=4,
                line_pt=15,
            )
        )
    else:
        body.append(
            make_paragraph(
                text,
                bold=True,
                font="Calibri",
                size_pt=12,
                color="1F4D78",
                before_pt=8,
                after_pt=3,
                line_pt=14,
            )
        )


def add_table(
    body: ET.Element,
    rows: list[list[str]],
    widths: list[int],
    *,
    header_fill: str = "E8EEF5",
    header_bold: bool = True,
    font: str = "Calibri",
    size_pt: float = 10.5,
) -> None:
    tbl = ET.SubElement(body, qn("w", "tbl"))
    tblPr = ET.SubElement(tbl, qn("w", "tblPr"))
    tblW = ET.SubElement(tblPr, qn("w", "tblW"))
    tblW.set(qn("w", "w"), str(sum(widths)))
    tblW.set(qn("w", "type"), "dxa")
    tblInd = ET.SubElement(tblPr, qn("w", "tblInd"))
    tblInd.set(qn("w", "w"), "120")
    tblInd.set(qn("w", "type"), "dxa")
    tblLook = ET.SubElement(tblPr, qn("w", "tblLook"))
    tblLook.set(qn("w", "firstRow"), "1")
    tblLook.set(qn("w", "lastRow"), "0")
    tblLook.set(qn("w", "firstColumn"), "1")
    tblLook.set(qn("w", "lastColumn"), "0")
    tblLook.set(qn("w", "noHBand"), "0")
    tblLook.set(qn("w", "noVBand"), "1")
    tblBorders = ET.SubElement(tblPr, qn("w", "tblBorders"))
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        edge_el = ET.SubElement(tblBorders, qn("w", edge))
        edge_el.set(qn("w", "val"), "single")
        edge_el.set(qn("w", "sz"), "6")
        edge_el.set(qn("w", "space"), "0")
        edge_el.set(qn("w", "color"), "C6CFDB")
    tblGrid = ET.SubElement(tbl, qn("w", "tblGrid"))
    for width in widths:
        ET.SubElement(tblGrid, qn("w", "gridCol")).set(qn("w", "w"), str(width))

    for r_idx, row in enumerate(rows):
        tr = ET.SubElement(tbl, qn("w", "tr"))
        for c_idx, cell_text in enumerate(row):
            tc = ET.SubElement(tr, qn("w", "tc"))
            tcPr = ET.SubElement(tc, qn("w", "tcPr"))
            tcW = ET.SubElement(tcPr, qn("w", "tcW"))
            tcW.set(qn("w", "w"), str(widths[c_idx]))
            tcW.set(qn("w", "type"), "dxa")
            tcMar = ET.SubElement(tcPr, qn("w", "tcMar"))
            for side, val in (("top", 80), ("bottom", 80), ("start", 120), ("end", 120)):
                m = ET.SubElement(tcMar, qn("w", side))
                m.set(qn("w", "w"), str(val))
                m.set(qn("w", "type"), "dxa")
            if r_idx == 0 and header_fill:
                shd = ET.SubElement(tcPr, qn("w", "shd"))
                shd.set(qn("w", "val"), "clear")
                shd.set(qn("w", "color"), "auto")
                shd.set(qn("w", "fill"), header_fill)

            p = ET.SubElement(tc, qn("w", "p"))
            pPr = ET.SubElement(p, qn("w", "pPr"))
            spacing = ET.SubElement(pPr, qn("w", "spacing"))
            spacing.set(qn("w", "before"), "0")
            spacing.set(qn("w", "after"), "0")
            spacing.set(qn("w", "line"), "240")
            spacing.set(qn("w", "lineRule"), "auto")
            if c_idx == 0:
                ET.SubElement(pPr, qn("w", "jc")).set(qn("w", "val"), "left")
            else:
                ET.SubElement(pPr, qn("w", "jc")).set(qn("w", "val"), "left")

            if "\n" in cell_text:
                parts = cell_text.split("\n")
            else:
                parts = [cell_text]
            for i, part in enumerate(parts):
                if i > 0:
                    p = ET.SubElement(tc, qn("w", "p"))
                    pPr = ET.SubElement(p, qn("w", "pPr"))
                    spacing = ET.SubElement(pPr, qn("w", "spacing"))
                    spacing.set(qn("w", "before"), "0")
                    spacing.set(qn("w", "after"), "0")
                    spacing.set(qn("w", "line"), "240")
                    spacing.set(qn("w", "lineRule"), "auto")
                p.append(
                    make_run(
                        part,
                        bold=header_bold if r_idx == 0 else False,
                        font=font,
                        size_pt=size_pt,
                        color="1F1F1F",
                    )
                )
    body.append(tbl)


def add_code_block(body: ET.Element, lines: list[str], title: str | None = None) -> None:
    if title:
        body.append(
            make_paragraph(
                title,
                bold=True,
                font="Calibri",
                size_pt=11,
                color="2E74B5",
                before_pt=8,
                after_pt=3,
                line_pt=13,
            )
        )
    tbl = ET.SubElement(body, qn("w", "tbl"))
    tblPr = ET.SubElement(tbl, qn("w", "tblPr"))
    tblW = ET.SubElement(tblPr, qn("w", "tblW"))
    tblW.set(qn("w", "w"), "9360")
    tblW.set(qn("w", "type"), "dxa")
    tblInd = ET.SubElement(tblPr, qn("w", "tblInd"))
    tblInd.set(qn("w", "w"), "0")
    tblInd.set(qn("w", "type"), "dxa")
    tblBorders = ET.SubElement(tblPr, qn("w", "tblBorders"))
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        edge_el = ET.SubElement(tblBorders, qn("w", edge))
        edge_el.set(qn("w", "val"), "single")
        edge_el.set(qn("w", "sz"), "4")
        edge_el.set(qn("w", "space"), "0")
        edge_el.set(qn("w", "color"), "D8DEE8")
    tblGrid = ET.SubElement(tbl, qn("w", "tblGrid"))
    ET.SubElement(tblGrid, qn("w", "gridCol")).set(qn("w", "w"), "9360")

    tr = ET.SubElement(tbl, qn("w", "tr"))
    tc = ET.SubElement(tr, qn("w", "tc"))
    tcPr = ET.SubElement(tc, qn("w", "tcPr"))
    tcW = ET.SubElement(tcPr, qn("w", "tcW"))
    tcW.set(qn("w", "w"), "9360")
    tcW.set(qn("w", "type"), "dxa")
    tcMar = ET.SubElement(tcPr, qn("w", "tcMar"))
    for side, val in (("top", 140), ("bottom", 140), ("start", 160), ("end", 160)):
        m = ET.SubElement(tcMar, qn("w", side))
        m.set(qn("w", "w"), str(val))
        m.set(qn("w", "type"), "dxa")
    shd = ET.SubElement(tcPr, qn("w", "shd"))
    shd.set(qn("w", "val"), "clear")
    shd.set(qn("w", "color"), "auto")
    shd.set(qn("w", "fill"), "F4F6F9")
    for idx, line in enumerate(lines):
        p = ET.SubElement(tc, qn("w", "p"))
        pPr = ET.SubElement(p, qn("w", "pPr"))
        spacing = ET.SubElement(pPr, qn("w", "spacing"))
        spacing.set(qn("w", "before"), "0")
        spacing.set(qn("w", "after"), "0")
        spacing.set(qn("w", "line"), "220")
        spacing.set(qn("w", "lineRule"), "auto")
        p.append(
            make_run(
                line,
                font="Courier New",
                size_pt=9.2,
                color="1F1F1F",
                monospace=True,
            )
        )
    body.append(tbl)


def add_text(body: ET.Element, text: str, *, after_pt: float = 6, before_pt: float = 0, size_pt: float = 11, color: str = "1F1F1F") -> None:
    body.append(
        make_paragraph(
            text,
            font="Calibri",
            size_pt=size_pt,
            color=color,
            before_pt=before_pt,
            after_pt=after_pt,
            line_pt=14,
        )
    )


def add_section_break(body: ET.Element) -> None:
    body.append(make_paragraph("", after_pt=3))


def build_document_xml() -> bytes:
    document = ET.Element(qn("w", "document"))
    body = ET.SubElement(document, qn("w", "body"))

    add_title_paragraph(body, "VoiceDesk AI")
    add_subtitle(
        body,
        "Project documentation for the live voice intake, simulated helpdesk backend, multi-agent handoff flow, and post-call QA review.",
    )
    add_text(
        body,
        "This document summarizes the architecture, the reason each tool is used, the agent roster, routing behavior, and example prompts for the ElevenLabs setup used by this repository.",
        after_pt=8,
        size_pt=11,
        color="3B3B3B",
    )

    add_heading(body, "At A Glance", 1)
    add_table(
        body,
        [
            ["Area", "Summary"],
            ["Primary user experience", "Live browser-based employee IT support call with multi-agent handoff."],
            ["Demo backend", "FastAPI service that simulates employee verification, incidents, ticketing, and post-call review."],
            ["UI layer", "Streamlit dashboard for scenario control, transcript review, handoff visualization, and structured QA output."],
            ["AI orchestration", "ElevenLabs handles the live voice conversation; Nebius adds optional summarization, routing, review, and escalation drafting."],
        ],
        [2200, 7160],
    )

    add_heading(body, "Architecture", 1)
    add_text(
        body,
        "The architecture is intentionally split into a live voice front door, a lightweight control plane, and a simulated helpdesk backend. This keeps the demo easy to explain during a presentation while still showing realistic agent specialization and handoff boundaries.",
        after_pt=8,
        color="3B3B3B",
    )
    add_code_block(
        body,
        [
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
        ],
    )

    add_heading(body, "Tools Used And Why", 1)
    add_table(
        body,
        [
            ["Tool", "Why it is used", "Where it appears in the repo"],
            ["ElevenLabs Conversational AI", "Live voice interaction layer, turn-taking, and agent handoffs.", "Configured externally; live session URL is loaded from `.env`."],
            ["FastAPI", "Simulated helpdesk backend and webhook receiver for verification, incidents, tickets, and post-call review.", "See `api.py`."],
            ["Streamlit", "Operator-facing demo UI with scenario selection, transcript, handoff cards, review panel, and backend status.", "See `app.py`."],
            ["Nebius", "Optional AI support for transcript summarization, routing guidance, QA review, and escalation drafting.", "See `src/nebius_client.py` and `src/service.py`."],
            ["Markdown runbooks", "Small knowledge base for guided troubleshooting and RAG-style resolution support.", "See `runbooks/`."],
            ["ngrok or a public deployment", "Makes the local webhook endpoints reachable from ElevenLabs when testing live.", "Used outside the repo when running locally."],
        ],
        [1800, 4700, 2860],
    )

    add_heading(body, "Agent Roster", 1)
    add_text(
        body,
        "The demo is built around four live agents plus one backend review step. The live agents are specialized so each one has a narrow job and a clear handoff responsibility.",
        after_pt=8,
        color="3B3B3B",
    )
    add_table(
        body,
        [
            ["Agent", "Primary job", "Key tools", "Handoff rule"],
            ["IT Intake Orchestrator", "Greet the caller, capture the issue, and route only after the problem is stated.", "Conversation flow, optional workflow/procedure, incident lookup.", "Stays in intake until it hears a real issue statement."],
            ["Employee Verification", "Confirm caller identity and basic employee details.", "POST /employees/verify.", "Moves forward only after verification succeeds or a restricted path is chosen."],
            ["IT Resolution Specialist", "Use runbooks to attempt a safe fix.", "GET /incidents/{category}; knowledge base runbooks.", "Escalates if the issue remains unresolved or if a known incident is active."],
            ["IT Escalation Coordinator", "Create a ticket and summarize what was tried.", "POST /tickets.", "Ends the live call after escalation details are confirmed."],
            ["Post-call Review", "Generate structured QA review data.", "POST /webhooks/elevenlabs/post-call.", "Runs after the call, not during the live voice flow."],
        ],
        [1960, 2400, 2720, 2280],
    )

    add_heading(body, "Agent Deep Dive", 1)

    deep_dive = [
        (
            "IT Intake Orchestrator",
            [
                "Purpose: this agent is the live front door. It greets the employee, asks what is wrong, and holds the conversation open until the issue is actually stated.",
                "Routing logic: do not hand off during the greeting turn. If the caller only says hello or provides identity details, stay in intake and ask one follow-up question. Route to verification or triage only after the issue is explicit.",
            ],
            [
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
            ],
        ),
        (
            "Employee Verification",
            [
                "Purpose: confirm the caller is the right employee and collect the minimum details needed for support actions.",
                "Routing logic: if verification succeeds, continue to triage or resolution. If it fails, move to a restricted path and avoid sensitive actions.",
            ],
            [
                "You are the Verification Agent for employee IT support.",
                "",
                "Goals:",
                "- Confirm the employee's identity using the provided details.",
                "- Ask for one missing field at a time if needed.",
                "- Verify name, employee ID, department, and manager when available.",
                "- If verification fails, keep the caller in a restricted support path.",
                "- If verification succeeds, route to triage or resolution.",
                "- Never resolve issues that require identity verification before confirmation.",
            ],
        ),
        (
            "IT Resolution Specialist",
            [
                "Purpose: attempt a safe guided fix using the small runbook set in the repository.",
                "Routing logic: if an active incident exists, do not waste time on local troubleshooting. If the issue is not resolved after the runbook steps, escalate with the attempted steps included.",
            ],
            [
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
            ],
        ),
        (
            "IT Escalation Coordinator",
            [
                "Purpose: capture the final summary, create the ticket, and close the live call professionally.",
                "Routing logic: once a ticket is created and the next support path is clear, do not bounce back to earlier agents unless the demo explicitly needs it.",
            ],
            [
                "You are the Escalation Coordinator for employee IT support.",
                "",
                "Goals:",
                "- Capture a concise issue summary.",
                "- Capture what was already tried.",
                "- Create a ticket with the right priority.",
                "- State the next support path clearly.",
                "- Reassure the employee about next steps.",
                "- End the live call after escalation details are confirmed.",
            ],
        ),
        (
            "Post-call Review",
            [
                "Purpose: produce structured QA output after the call ends.",
                "Routing logic: this is a backend-only step. It consumes the transcript and call state from the webhook and writes a review summary used by the Streamlit dashboard.",
            ],
            [
                "The review step is not a live voice agent.",
                "It is a webhook-backed backend step that receives the completed call transcript and call state.",
                "It then generates a review record with resolution status, verification status, escalation status, follow-up status, and QA notes.",
            ],
        ),
    ]

    for title, paragraphs, prompt_lines in deep_dive:
        add_heading(body, title, 2)
        for paragraph in paragraphs:
            add_text(body, paragraph, after_pt=4, color="2D2D2D")
        add_code_block(body, prompt_lines, title="Sample prompt")

    add_heading(body, "Routing Logic", 1)
    add_text(
        body,
        "The routing model is intentionally simple so the demo is explainable in a presentation. Each agent has a small decision boundary and a single primary output.",
        after_pt=8,
        color="3B3B3B",
    )
    add_table(
        body,
        [
            ["Step", "Condition", "Next agent", "Notes"],
            ["1", "Caller has not stated the issue yet.", "Stay in intake", "Ask for the issue; do not transfer on greeting alone."],
            ["2", "Issue is stated and identity details are needed.", "Employee Verification", "Collect name, employee ID, department, and manager."],
            ["3", "Issue is an individual problem and no active incident exists.", "IT Resolution Specialist", "Use the runbook and KB."],
            ["4", "Active incident exists or runbook fails.", "IT Escalation Coordinator", "Create ticket and hand off cleanly."],
            ["5", "Call ends.", "Post-call review webhook", "Generate the structured QA record."],
        ],
        [800, 2900, 2600, 3060],
    )

    add_heading(body, "Repository Map", 1)
    add_table(
        body,
        [
            ["File", "Role"],
            ["app.py", "Streamlit user interface, live status badges, transcript view, handoff dashboard, and review panel."],
            ["api.py", "FastAPI service that receives verification, incident lookup, ticketing, and post-call webhook requests."],
            ["src/service.py", "Call-state engine and deterministic support workflow used by the demo."],
            ["src/scenarios.py", "Scenario definitions used to simulate different employee IT support calls."],
            ["src/nebius_client.py", "Optional Nebius-backed helpers for summarization, routing, review, and escalation drafting."],
            ["runbooks/*.md", "Small support knowledge base used by the resolution agent."],
        ],
        [2200, 7160],
    )

    add_heading(body, "Environment Variables", 1)
    add_text(
        body,
        "The live demo is configured through `.env`. The UI reads these values at startup so keys do not need to be typed into the app.",
        after_pt=6,
        color="3B3B3B",
    )
    add_table(
        body,
        [
            ["Variable", "Purpose"],
            ["ELEVENLABS_API_KEY", "Enables ElevenLabs connectivity."],
            ["ELEVENLABS_AGENT_ID", "Identifies the live voice agent."],
            ["ELEVENLABS_WEBHOOK_URL", "Public webhook target for post-call or tool callbacks."],
            ["ELEVENLABS_WEB_VOICE_URL", "Live browser session URL for the voice experience."],
            ["NEBIUS_API_KEY", "Optional AI helper access."],
            ["NEBIUS_MODEL", "Model name used by the Nebius client."],
            ["NEBIUS_BASE_URL", "OpenAI-compatible Nebius API base URL."],
        ],
        [2800, 6560],
    )

    add_heading(body, "Closing Summary", 1)
    add_text(
        body,
        "This project demonstrates a realistic employee IT support workflow where specialized agents collaborate instead of a single general-purpose assistant doing everything. The design keeps the demo approachable for a live presentation while still showing concrete orchestration, tool usage, routing rules, and structured post-call QA.",
        after_pt=0,
        color="3B3B3B",
    )

    sectPr = ET.SubElement(body, qn("w", "sectPr"))
    pgSz = ET.SubElement(sectPr, qn("w", "pgSz"))
    pgSz.set(qn("w", "w"), "12240")
    pgSz.set(qn("w", "h"), "15840")
    pgMar = ET.SubElement(sectPr, qn("w", "pgMar"))
    for side, val in (("top", 1440), ("right", 1440), ("bottom", 1440), ("left", 1440), ("header", 708), ("footer", 708), ("gutter", 0)):
        pgMar.set(qn("w", side), str(val))

    return ET.tostring(document, encoding="utf-8", xml_declaration=True)


def build_styles_xml() -> bytes:
    styles = ET.Element(qn("w", "styles"))
    docDefaults = ET.SubElement(styles, qn("w", "docDefaults"))
    rPrDefault = ET.SubElement(docDefaults, qn("w", "rPrDefault"))
    rPr = ET.SubElement(rPrDefault, qn("w", "rPr"))
    rFonts = ET.SubElement(rPr, qn("w", "rFonts"))
    rFonts.set(qn("w", "ascii"), "Calibri")
    rFonts.set(qn("w", "hAnsi"), "Calibri")
    ET.SubElement(rPr, qn("w", "sz")).set(qn("w", "val"), "22")
    ET.SubElement(rPr, qn("w", "szCs")).set(qn("w", "val"), "22")
    ET.SubElement(rPr, qn("w", "color")).set(qn("w", "val"), "000000")
    pPrDefault = ET.SubElement(docDefaults, qn("w", "pPrDefault"))
    pPr = ET.SubElement(pPrDefault, qn("w", "pPr"))
    spacing = ET.SubElement(pPr, qn("w", "spacing"))
    spacing.set(qn("w", "before"), "0")
    spacing.set(qn("w", "after"), "120")
    spacing.set(qn("w", "line"), "240")
    spacing.set(qn("w", "lineRule"), "auto")

    def add_style(style_id: str, name: str, size: int, color: str, bold: bool = False):
        style = ET.SubElement(styles, qn("w", "style"))
        style.set(qn("w", "type"), "paragraph")
        style.set(qn("w", "styleId"), style_id)
        ET.SubElement(style, qn("w", "name")).set(qn("w", "val"), name)
        pPr = ET.SubElement(style, qn("w", "pPr"))
        spacing = ET.SubElement(pPr, qn("w", "spacing"))
        spacing.set(qn("w", "before"), "0")
        spacing.set(qn("w", "after"), "120")
        spacing.set(qn("w", "line"), "240")
        spacing.set(qn("w", "lineRule"), "auto")
        rPr = ET.SubElement(style, qn("w", "rPr"))
        if bold:
            ET.SubElement(rPr, qn("w", "b"))
        ET.SubElement(rPr, qn("w", "sz")).set(qn("w", "val"), str(size))
        ET.SubElement(rPr, qn("w", "szCs")).set(qn("w", "val"), str(size))
        ET.SubElement(rPr, qn("w", "color")).set(qn("w", "val"), color)
        fonts = ET.SubElement(rPr, qn("w", "rFonts"))
        fonts.set(qn("w", "ascii"), "Calibri")
        fonts.set(qn("w", "hAnsi"), "Calibri")
    add_style("Normal", "Normal", 22, "000000")
    add_style("Heading1", "Heading 1", 32, "2E74B5", True)
    add_style("Heading2", "Heading 2", 26, "2E74B5", True)
    add_style("Heading3", "Heading 3", 24, "1F4D78", True)
    add_style("Title", "Title", 48, "1F1F1F", True)
    return ET.tostring(styles, encoding="utf-8", xml_declaration=True)


def build_core_props_xml() -> bytes:
    now = date.today().isoformat()
    root = ET.Element(qn("cp", "coreProperties"))
    ET.SubElement(root, qn("dc", "title")).text = "VoiceDesk AI"
    ET.SubElement(root, qn("dc", "subject")).text = "Project documentation"
    ET.SubElement(root, qn("dc", "creator")).text = "Ayush Narayan"
    ET.SubElement(root, qn("cp", "keywords")).text = "voice ai, multi-agent, helpdesk, elevenlabs, fastapi, streamlit"
    ET.SubElement(root, qn("dc", "description")).text = "Architecture, tools, agents, routing logic, and sample prompts for VoiceDesk AI, the multi-agent IT support voice assistant."
    ET.SubElement(root, qn("cp", "lastModifiedBy")).text = "Ayush Narayan"
    ET.SubElement(root, qn("cp", "revision")).text = "1"
    created = ET.SubElement(root, qn("dcterms", "created"))
    created.set(qn("xsi", "type"), "dcterms:W3CDTF")
    created.text = f"{now}T00:00:00Z"
    modified = ET.SubElement(root, qn("dcterms", "modified"))
    modified.set(qn("xsi", "type"), "dcterms:W3CDTF")
    modified.text = f"{now}T00:00:00Z"
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def build_app_props_xml() -> bytes:
    root = ET.Element("{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Properties")
    ET.SubElement(root, "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Application").text = "Microsoft Office Word"
    ET.SubElement(root, "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}DocSecurity").text = "0"
    ET.SubElement(root, "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}ScaleCrop").text = "false"
    ET.SubElement(root, "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}HeadingPairs")
    ET.SubElement(root, "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}TitlesOfParts")
    ET.SubElement(root, "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Company").text = ""
    ET.SubElement(root, "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}LinksUpToDate").text = "false"
    ET.SubElement(root, "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}SharedDoc").text = "false"
    ET.SubElement(root, "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}HyperlinksChanged").text = "false"
    ET.SubElement(root, "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}AppVersion").text = "16.0000"
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def build_content_types_xml() -> bytes:
    root = ET.Element("{http://schemas.openxmlformats.org/package/2006/content-types}Types")
    defaults = [
        ("rels", "application/vnd.openxmlformats-package.relationships+xml"),
        ("xml", "application/xml"),
    ]
    for ext, ctype in defaults:
        el = ET.SubElement(root, "{http://schemas.openxmlformats.org/package/2006/content-types}Default")
        el.set("Extension", ext)
        el.set("ContentType", ctype)
    overrides = [
        ("/word/document.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"),
        ("/word/styles.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"),
        ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
        ("/docProps/app.xml", "application/vnd.openxmlformats-officedocument.extended-properties+xml"),
    ]
    for part, ctype in overrides:
        el = ET.SubElement(root, "{http://schemas.openxmlformats.org/package/2006/content-types}Override")
        el.set("PartName", part)
        el.set("ContentType", ctype)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def build_rels_xml() -> bytes:
    root = ET.Element("Relationships", xmlns="http://schemas.openxmlformats.org/package/2006/relationships")
    rel = ET.SubElement(root, "Relationship")
    rel.set("Id", "rId1")
    rel.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument")
    rel.set("Target", "word/document.xml")
    rel2 = ET.SubElement(root, "Relationship")
    rel2.set("Id", "rId2")
    rel2.set("Type", "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties")
    rel2.set("Target", "docProps/core.xml")
    rel3 = ET.SubElement(root, "Relationship")
    rel3.set("Id", "rId3")
    rel3.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties")
    rel3.set("Target", "docProps/app.xml")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def build_document_rels_xml() -> bytes:
    root = ET.Element("Relationships", xmlns="http://schemas.openxmlformats.org/package/2006/relationships")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def build_docx(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    parts = {
        "[Content_Types].xml": build_content_types_xml(),
        "_rels/.rels": build_rels_xml(),
        "docProps/core.xml": build_core_props_xml(),
        "docProps/app.xml": build_app_props_xml(),
        "word/document.xml": build_document_xml(),
        "word/styles.xml": build_styles_xml(),
        "word/_rels/document.xml.rels": build_document_rels_xml(),
    }
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, data in parts.items():
            zf.writestr(path, data)


if __name__ == "__main__":
    build_docx(OUT_PATH)
    print(OUT_PATH)
