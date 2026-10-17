from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.promptfoo_harness import render_promptfoo_output
from src.local_env import load_local_env
from src.service import HelpdeskService, redact_internal_annotations


load_local_env()

app = FastAPI(title="VoiceDesk AI API")
service = HelpdeskService()


class EmployeeVerificationRequest(BaseModel):
    employee_name: str
    employee_id: str | None = None
    department: str | None = None
    manager: str | None = None


class TicketCreateRequest(BaseModel):
    caller_name: str
    employee_id: str | None = None
    category: str
    summary: str
    priority: str = Field(default="medium")
    verification_status: str = Field(default="unverified")
    attempted_steps: list[str] = Field(default_factory=list)


class PromptfooStressTestRequest(BaseModel):
    prompt: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/employees/verify")
def verify_employee(payload: EmployeeVerificationRequest) -> dict:
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    return service.verify_employee(data)


@app.get("/incidents/{category}")
def incident_status(category: str) -> dict:
    return service.get_incident_status(category)


@app.post("/tickets")
def create_ticket(payload: TicketCreateRequest) -> dict:
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    try:
        return service.create_ticket(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/webhooks/elevenlabs/post-call")
def elevenlabs_post_call(payload: dict[str, Any]) -> dict:
    normalized = normalize_post_call_payload(payload)
    return service.build_review(
        call_id=normalized["call_id"],
        transcript=normalized["transcript"],
        state=normalized["state"],
    )


def normalize_post_call_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Accept both the demo payload and the real ElevenLabs post-call transcription payload.
    """
    if isinstance(payload.get("data"), dict):
        data = payload["data"]
        call_id = (
            data.get("conversation_id")
            or data.get("call_id")
            or payload.get("conversation_id")
            or payload.get("call_id")
            or "unknown"
        )
        transcript = normalize_transcript(
            data.get("transcript")
            or data.get("conversation")
            or data.get("messages")
            or payload.get("transcript")
            or []
        )
        state = payload.get("state") if isinstance(payload.get("state"), dict) else {}
        state = {
            **state,
            "analysis": data.get("analysis", {}),
            "metadata": data.get("metadata", {}),
            "conversation_initiation_client_data": data.get("conversation_initiation_client_data", {}),
            "event_timestamp": payload.get("event_timestamp"),
            "webhook_type": payload.get("type", "post_call_transcription"),
        }
        if "issue_category" not in state:
            state["issue_category"] = infer_issue_category(state, transcript)
        return {"call_id": str(call_id), "transcript": transcript, "state": state}

    call_id = payload.get("call_id") or payload.get("conversation_id") or "unknown"
    transcript = normalize_transcript(payload.get("transcript", []))
    state = payload.get("state") if isinstance(payload.get("state"), dict) else {}
    if "issue_category" not in state:
        state["issue_category"] = infer_issue_category(state, transcript)
    return {"call_id": str(call_id), "transcript": transcript, "state": state}


@app.post("/promptfoo/stress-test")
def promptfoo_stress_test(payload: PromptfooStressTestRequest) -> dict[str, str]:
    return {"output": render_promptfoo_output(payload.prompt)}


def normalize_transcript(raw: Any) -> list[dict[str, str]]:
    if isinstance(raw, dict):
        for key in ("turns", "messages", "transcript", "items", "utterances"):
            if isinstance(raw.get(key), list):
                return normalize_transcript(raw[key])
        return []

    if not isinstance(raw, list):
        if isinstance(raw, str) and raw.strip():
            return [{"speaker": "system", "text": raw, "timestamp": ""}]
        return []

    normalized: list[dict[str, str]] = []
    for item in raw:
        if isinstance(item, dict):
            speaker = (
                item.get("speaker")
                or item.get("role")
                or item.get("agent")
                or item.get("name")
                or "unknown"
            )
            text = item.get("text") or item.get("content") or item.get("message") or ""
            timestamp = (
                item.get("timestamp")
                or item.get("time")
                or item.get("created_at")
                or item.get("event_timestamp")
                or ""
            )
            normalized.append(
                {
                    "speaker": str(speaker),
                    "text": redact_internal_annotations(str(text)),
                    "timestamp": str(timestamp),
                }
            )
        elif isinstance(item, str) and item.strip():
            normalized.append({"speaker": "unknown", "text": redact_internal_annotations(item), "timestamp": ""})
    return normalized


def infer_issue_category(state: dict[str, Any], transcript: list[dict[str, str]]) -> str:
    text_blob = " ".join(
        [
            str(state.get("issue_category", "")),
            str(state.get("summary", "")),
            " ".join(turn.get("text", "") for turn in transcript),
        ]
    ).lower()
    for category in ("vpn", "mfa", "password_reset", "email", "billing"):
        if category in text_blob:
            return category
    return "unknown"
