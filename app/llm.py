import json
import os
from typing import Optional
from pydantic import ValidationError
import requests
from app.config import GEMINI_API_KEY, REQUEST_TIMEOUT
from app.schemas import Finding, LLMExplanation

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, timeout: int = REQUEST_TIMEOUT):
        self.api_key = api_key if api_key is not None else GEMINI_API_KEY
        self.timeout = timeout

    def generate(self, prompt: str, timeout: Optional[int] = None) -> str:
        key = self.api_key or os.getenv("GEMINI_API_KEY", "")
        if not key:
            raise ValueError("GEMINI_API_KEY is not configured")

        effective_timeout = timeout if timeout is not None else self.timeout
        url = f"{GEMINI_API_URL}?key={key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        response = requests.post(url, json=payload, timeout=effective_timeout)
        response.raise_for_status()

        data = response.json()
        try:
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return ""
        except (KeyError, IndexError) as e:
            raise ValueError(f"Unexpected response structure from Gemini API: {e}") from e


def generate(prompt: str, timeout: Optional[int] = None) -> str:
    """Generate completion using Gemini client reading GEMINI_API_KEY with a timeout."""
    client = GeminiClient()
    return client.generate(prompt, timeout=timeout)


def _clean_json_str(text: str) -> str:
    """Strip markdown code formatting if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def explain_finding(finding: Finding, code: str) -> LLMExplanation:
    """
    Generate structured explanation and suggested fix for a finding.
    Validates JSON and retries once on invalid output.
    """
    prompt = (
        f"You are a Python security expert analyzing dependency risks.\n\n"
        f"Finding details:\n"
        f"- Package: {finding.package}\n"
        f"- Verdict: {finding.verdict}\n"
        f"- Risk score: {finding.risk_score}\n"
        f"- Reasons: {'; '.join(finding.reasons)}\n"
        f"- Suggested fix: {finding.suggested_fix or 'None'}\n\n"
        f"User code:\n```python\n{code}\n```\n\n"
        f"Explain why this dependency is risky and suggest a fix.\n"
        f"Return ONLY a JSON object with keys 'explanation' (string) and 'suggested_fix' (string or null)."
    )

    last_error = None
    for attempt in range(2):
        current_prompt = prompt if attempt == 0 else (
            f"{prompt}\n\nCRITICAL: Previous response was not valid JSON. "
            f"Respond ONLY with valid JSON with keys 'explanation' and 'suggested_fix'."
        )
        try:
            raw_text = generate(current_prompt)
            cleaned = _clean_json_str(raw_text)
            data = json.loads(cleaned)
            return LLMExplanation(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e

    raise ValueError(f"Failed to produce valid LLMExplanation after retry: {last_error}")
