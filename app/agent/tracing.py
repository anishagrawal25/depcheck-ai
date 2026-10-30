import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
TRACES_FILE = os.path.join(LOGS_DIR, "traces.jsonl")

_LANGFUSE_CLIENT = None


def get_langfuse():
    """Retrieve Langfuse client if API keys are configured and package installed."""
    global _LANGFUSE_CLIENT
    if _LANGFUSE_CLIENT is not None:
        return _LANGFUSE_CLIENT

    pub_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    sec_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if pub_key and sec_key:
        try:
            from langfuse import Langfuse

            _LANGFUSE_CLIENT = Langfuse(public_key=pub_key, secret_key=sec_key, host=host)
            return _LANGFUSE_CLIENT
        except (ImportError, Exception):
            pass
    return None


def log_agent_step(
    tool: str,
    latency: float,
    tokens: Optional[int] = None,
    status: str = "success",
    args: Optional[Dict[str, Any]] = None,
    output: Optional[Any] = None,
    file_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Log an agent step to logs/traces.jsonl and optionally send to Langfuse.
    """
    target_file = file_path or TRACES_FILE
    os.makedirs(os.path.dirname(target_file), exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "latency": round(latency, 4),
        "tokens": tokens,
        "status": status,
        "args": args or {},
        "output": str(output) if output is not None else None,
    }

    with open(target_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    langfuse = get_langfuse()
    if langfuse is not None:
        try:
            langfuse.trace(
                name=f"agent-tool-{tool}",
                metadata=record,
            )
        except Exception:
            pass

    return record
