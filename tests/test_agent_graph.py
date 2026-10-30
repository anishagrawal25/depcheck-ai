from typing import Any, List, Optional
from unittest.mock import patch
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from app.agent.graph import build_investigation_graph, investigate_package
from app.schemas import Finding


class ScriptedFakeLLM(BaseChatModel):
    responses: List[AIMessage]
    index: int = 0

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        if self.index < len(self.responses):
            resp = self.responses[self.index]
            self.index += 1
            return ChatResult(generations=[ChatGeneration(message=resp)])
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="Done"))])

    @property
    def _llm_type(self) -> str:
        return "scripted_fake_llm"

    def bind_tools(self, tools: List[Any], **kwargs: Any) -> "ScriptedFakeLLM":
        return self


def test_investigate_package_ok_bypasses_graph():
    finding = Finding(
        package="requests",
        verdict="ok",
        risk_score=0.0,
        confidence=0.85,
        reasons=[],
    )
    result = investigate_package(finding, "import requests")
    assert result == finding
    assert result.confidence == 0.85


def test_investigate_package_suspicious_runs_graph():
    finding = Finding(
        package="reqeusts",
        verdict="suspicious",
        risk_score=0.6,
        confidence=0.85,
        reasons=["Name is similar to requests"],
        suggested_fix="Did you mean 'requests'?",
    )
    result = investigate_package(finding, "import reqeusts")
    assert result.package == "reqeusts"
    assert result.verdict == "suspicious"
    assert result.confidence > 0.85
    assert result.suggested_fix == "Did you mean 'requests'?"
    assert any("Agent analysis" in r for r in result.reasons)


def test_agent_graph_scripted_fake_llm():
    step1 = AIMessage(
        content="",
        tool_calls=[{
            "id": "c1",
            "name": "find_similar_package",
            "args": {"package": "reqeusts"},
        }],
    )
    step2 = AIMessage(content="Package reqeusts is a typosquat for requests.")
    fake_llm = ScriptedFakeLLM(responses=[step1, step2])

    finding = Finding(
        package="reqeusts",
        verdict="suspicious",
        risk_score=0.6,
        confidence=0.7,
        reasons=["Initial suspicious flags"],
    )
    result = investigate_package(finding, "import reqeusts", llm=fake_llm)
    assert result.package == "reqeusts"
    assert result.suggested_fix == "Did you mean 'requests'?"
    assert any("typosquat for requests" in r for r in result.reasons)


def test_agent_graph_tool_call_cap():
    many_calls = [
        {"id": f"c_{i}", "name": "find_similar_package", "args": {"package": "testpkg"}}
        for i in range(8)
    ]
    step1 = AIMessage(content="", tool_calls=many_calls)
    step2 = AIMessage(content="Investigation complete.")
    fake_llm = ScriptedFakeLLM(responses=[step1, step2])

    finding = Finding(
        package="testpkg",
        verdict="suspicious",
        risk_score=0.6,
        confidence=0.5,
        reasons=[],
    )
    graph = build_investigation_graph(llm=fake_llm)
    state = {
        "finding": finding,
        "code": "import testpkg",
        "package": "testpkg",
        "tool_call_count": 0,
        "messages": [HumanMessage(content="Investigate")],
        "final_finding": None,
    }
    final_state = graph.invoke(state)
    assert final_state["tool_call_count"] == 6


def test_agent_graph_failing_tool():
    step1 = AIMessage(
        content="",
        tool_calls=[{
            "id": "c_fail",
            "name": "check_registry",
            "args": {"package": "failingpkg"},
        }],
    )
    step2 = AIMessage(content="Recovered from tool failure, confirmed suspicious.")
    fake_llm = ScriptedFakeLLM(responses=[step1, step2])

    finding = Finding(
        package="failingpkg",
        verdict="suspicious",
        risk_score=0.7,
        confidence=0.5,
        reasons=[],
    )
    with patch("app.agent.tools.get_package_signals", side_effect=RuntimeError("Database down")):
        result = investigate_package(finding, "import failingpkg", llm=fake_llm)
        assert result.package == "failingpkg"
        assert any("Recovered from tool failure" in r for r in result.reasons)
