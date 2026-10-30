import os
from typing import Optional
import requests
from app.config import GEMINI_API_KEY, REQUEST_TIMEOUT

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
