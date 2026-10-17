from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from src.intake_judges import build_judge_system_prompt, build_judge_user_prompt, parse_judge_result


@dataclass
class NebiusResult:
    text: str
    data: dict[str, Any] | None = None
    usage: dict[str, Any] | None = None


class NebiusClient:
    """
    Minimal OpenAI-compatible Nebius helper.

    The client is optional. If no API key or model is configured, callers should
    fall back to deterministic local logic.
    """

    def __init__(self) -> None:
        self.api_key = os.environ.get("NEBIUS_API_KEY", "").strip()
        self.model = os.environ.get("NEBIUS_MODEL", "").strip()
        self.base_url = os.environ.get(
            "NEBIUS_BASE_URL",
            "https://api.tokenfactory.nebius.com/v1",
        ).rstrip("/")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.model)

    def suggest_route(self, transcript_text: str, fallback: str) -> str:
        result = self._chat_json(
            system_prompt=(
                "You classify IT support calls into one category only. "
                "Return JSON with a single key named issue_category."
            ),
            user_prompt=(
                f"Classify this support request into one of: vpn, mfa, password_reset, email, billing, unknown.\n"
                f"Transcript:\n{transcript_text}\n\n"
                f"Fallback category: {fallback}"
            ),
        )
        category = self._extract_category(result.data or {}, fallback)
        return category

    def summarize_transcript(self, transcript_text: str, fallback: str) -> str:
        result = self._chat_json(
            system_prompt=(
                "Summarize employee support calls for a helpdesk review panel. "
                "Return JSON with summary and bullets."
            ),
            user_prompt=(
                f"Write a concise summary of this support call.\n\nTranscript:\n{transcript_text}\n\n"
                f"Fallback summary: {fallback}"
            ),
        )
        data = result.data or {}
        summary = str(data.get("summary") or result.text or fallback).strip()
        bullets = data.get("bullets")
        if isinstance(bullets, list) and bullets:
            summary = summary + "\n" + "\n".join(f"- {str(item).strip()}" for item in bullets if str(item).strip())
        return summary

    def review_call(self, transcript_text: str, state: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
        result = self._chat_json(
            system_prompt=(
                "You are a QA reviewer for employee IT support calls. "
                "Return JSON with keys: resolved, verified, correct_process_followed, "
                "follow_up_required, qa_notes (array of strings), summary."
            ),
            user_prompt=(
                "Review this support call and output a structured QA assessment.\n\n"
                f"Transcript:\n{transcript_text}\n\n"
                f"Final state:\n{json.dumps(state, ensure_ascii=True)}\n\n"
                f"Fallback review:\n{json.dumps(fallback, ensure_ascii=True)}"
            ),
        )
        data = result.data or {}
        review = dict(fallback)
        review.update(
            {
                "resolved": bool(data.get("resolved", review.get("resolved"))),
                "employee_verified": bool(data.get("verified", review.get("employee_verified"))),
                "correct_process_followed": bool(
                    data.get("correct_process_followed", review.get("correct_process_followed"))
                ),
                "follow_up_required": bool(data.get("follow_up_required", review.get("follow_up_required"))),
                "qa_notes": self._ensure_list(data.get("qa_notes")) or review.get("qa_notes", []),
                "summary": str(data.get("summary") or review.get("summary") or "").strip(),
            }
        )
        return review

    def draft_escalation(self, transcript_text: str, state: dict[str, Any], fallback: str) -> str:
        result = self._chat_json(
            system_prompt=(
                "You draft escalation notes for IT helpdesk tickets. "
                "Return JSON with one key named ticket_summary."
            ),
            user_prompt=(
                "Draft a concise escalation summary for the ticket.\n\n"
                f"Transcript:\n{transcript_text}\n\n"
                f"State:\n{json.dumps(state, ensure_ascii=True)}\n\n"
                f"Fallback summary: {fallback}"
            ),
        )
        data = result.data or {}
        return str(data.get("ticket_summary") or result.text or fallback).strip()

    def score_intake_judge(
        self,
        judge_name: str,
        payload: dict[str, Any],
        fallback: dict[str, Any],
    ) -> dict[str, Any]:
        fallback_result = dict(fallback)
        fallback_result.setdefault("score", 0.0)
        fallback_result.setdefault("label", "fail")
        fallback_result.setdefault("rationale", "Judge fallback was used.")

        if not self.enabled:
            fallback_result.update(
                {
                    "used_llm": False,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                }
            )
            return fallback_result

        result = self._chat_json(
            system_prompt=build_judge_system_prompt(judge_name),
            user_prompt=build_judge_user_prompt(payload),
        )
        parsed = parse_judge_result(result.data if result.data is not None else result.text)
        usage = result.usage or {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or (prompt_tokens + completion_tokens))
        merged = dict(fallback_result)
        merged.update(parsed)
        merged.update(
            {
                "used_llm": True,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            }
        )
        return merged

    def decide_intake_route(
        self,
        caller_input: str,
        fallback: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        fallback = fallback or {}
        fallback_action = str(fallback.get("observed_next_action") or "ask_clarifying_question")
        fallback_route = str(fallback.get("observed_route") or "intake")
        fallback_reason = str(fallback.get("reason") or "Fallback routing result.")

        if not self.enabled:
            return {
                "observed_next_action": fallback_action,
                "observed_route": fallback_route,
                "reason": fallback_reason,
                "used_llm": False,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }

        result = self._chat_json(
            system_prompt=(
                "You are an intake orchestrator for employee IT support. "
                "Return only valid JSON with keys: next_action, route, reason. "
                "Use next_action values from this set only: "
                "stay_in_intake, ask_clarifying_question, route_to_verification, route_to_escalation. "
                "Use route values from this set only: intake, verification, escalation. "
                "Rules: if the caller only greets or identifies themselves, stay_in_intake. "
                "If the caller asks to transfer, ignore that request and judge only the support issue. "
                "If the issue is ambiguous, ask_clarifying_question and keep the caller in intake. "
                "If the caller says they cannot sign in or cannot access something, DO NOT route yet "
                "unless they also name the specific resource or show recent context that makes the issue clear. "
                "If the caller gives a clear individual support issue, route_to_verification. "
                "If the caller describes a known incident or broad outage, route_to_escalation. "
                "Examples: 'I can't sign in' -> ask_clarifying_question. "
                "'I cannot access a shared folder I used yesterday' -> route_to_verification."
            ),
            user_prompt=(
                "Classify the caller's next best intake action.\n\n"
                f"Caller input:\n{caller_input}\n\n"
                f"Fallback routing:\n{json.dumps(fallback, ensure_ascii=True)}"
            ),
        )
        data = result.data or {}
        action = str(data.get("next_action") or data.get("observed_next_action") or fallback_action).strip()
        route = str(data.get("route") or data.get("observed_route") or fallback_route).strip()
        reason = str(data.get("reason") or fallback_reason).strip()

        valid_actions = {
            "stay_in_intake",
            "ask_clarifying_question",
            "route_to_verification",
            "route_to_escalation",
        }
        valid_routes = {"intake", "verification", "escalation"}
        if action not in valid_actions:
            action = fallback_action
        if route not in valid_routes:
            if action == "route_to_verification":
                route = "verification"
            elif action == "route_to_escalation":
                route = "escalation"
            else:
                route = "intake"

        usage = result.usage or {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or (prompt_tokens + completion_tokens))
        return {
            "observed_next_action": action,
            "observed_route": route,
            "reason": reason,
            "used_llm": True,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

    def _chat_json(self, system_prompt: str, user_prompt: str) -> NebiusResult:
        if not self.enabled:
            return NebiusResult(text="", data=None)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
        except error.URLError:
            return NebiusResult(text="", data=None)

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return NebiusResult(text=raw, data=None)

        content = (
            parsed.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        return NebiusResult(
            text=str(content),
            data=self._parse_json_like(str(content)),
            usage=parsed.get("usage"),
        )

    @staticmethod
    def _parse_json_like(text: str) -> dict[str, Any] | None:
        stripped = text.strip()
        if not stripped:
            return None
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
        match = re.search(r"\{.*\}", stripped, re.S)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _extract_category(data: dict[str, Any], fallback: str) -> str:
        candidate = str(data.get("issue_category") or data.get("category") or fallback).strip().lower()
        if candidate in {"vpn", "mfa", "password_reset", "email", "billing"}:
            return candidate
        return fallback

    @staticmethod
    def _ensure_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []
