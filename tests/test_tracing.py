import json
import os
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage
from app.agent.graph import investigate_package
from app.agent.tracing import log_agent_step
from app.schemas import Finding
from tests.test_agent_graph import ScriptedFakeLLM


def test_log_agent_step_creates_record(tmp_path):
    trace_file = str(tmp_path / "traces.jsonl")
    record = log_agent_step(
        tool="find_similar_package",
        latency=0.0456,
        tokens=15,
        status="success",
        args={"package": "reqeusts"},
        output="['requests']",
        file_path=trace_file,
    )

    assert record["tool"] == "find_similar_package"
    assert record["latency"] == 0.0456
    assert record["tokens"] == 15
    assert record["status"] == "success"
    assert record["args"] == {"package": "reqeusts"}
    assert record["output"] == "['requests']"
    assert "timestamp" in record

    assert os.path.exists(trace_file)
    with open(trace_file, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]
    assert len(lines) == 1
    assert lines[0]["tool"] == "find_similar_package"


def test_log_agent_step_appends(tmp_path):
    trace_file = str(tmp_path / "traces.jsonl")
    log_agent_step(tool="tool_a", latency=0.01, file_path=trace_file)
    log_agent_step(tool="tool_b", latency=0.02, file_path=trace_file)

    with open(trace_file, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]
    assert len(lines) == 2
    assert lines[0]["tool"] == "tool_a"
    assert lines[1]["tool"] == "tool_b"


def test_tools_node_logs_trace(tmp_path, monkeypatch):
    trace_file = str(tmp_path / "agent_traces.jsonl")
    monkeypatch.setattr("app.agent.tracing.TRACES_FILE", trace_file)

    step1 = AIMessage(
        content="",
        tool_calls=[{
            "id": "c1",
            "name": "find_similar_package",
            "args": {"package": "reqeusts"},
        }],
    )
    step2 = AIMessage(content="Identified typo.")
    fake_llm = ScriptedFakeLLM(responses=[step1, step2])

    finding = Finding(
        package="reqeusts",
        verdict="suspicious",
        risk_score=0.6,
        confidence=0.7,
        reasons=["Suspicious name"],
    )

    investigate_package(finding, "import reqeusts", llm=fake_llm)

    assert os.path.exists(trace_file)
    with open(trace_file, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    assert len(records) >= 1
    rec = records[0]
    assert rec["tool"] == "find_similar_package"
    assert rec["status"] == "success"
    assert rec["args"] == {"package": "reqeusts"}
    assert isinstance(rec["latency"], float)


def test_langfuse_integration_mock(monkeypatch, tmp_path):
    trace_file = str(tmp_path / "langfuse_traces.jsonl")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-mock")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-mock")

    mock_client = MagicMock()
    monkeypatch.setattr("app.agent.tracing._LANGFUSE_CLIENT", mock_client)

    log_agent_step(
        tool="check_registry",
        latency=0.05,
        status="success",
        args={"package": "requests"},
        file_path=trace_file,
    )

    assert mock_client.trace.called
    trace_call = mock_client.trace.call_args
    assert trace_call.kwargs["name"] == "agent-tool-check_registry"
    assert trace_call.kwargs["metadata"]["tool"] == "check_registry"
