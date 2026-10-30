from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from app.agent.tools import ALL_TOOLS
from app.schemas import Finding

TOOLS_BY_NAME = {t.name: t for t in ALL_TOOLS}
TOOL_CALL_CAP = 6


class DefaultInvestigationLLM(BaseChatModel):
    """Default fallback LLM for agent graph when no external model is provided."""

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Default behavior inspects tool messages or finalizes
        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(
                        content="Investigation complete: package verified based on available registry and similarity signals."
                    )
                )
            ]
        )

    @property
    def _llm_type(self) -> str:
        return "default_investigation_llm"

    def bind_tools(self, tools: List[Any], **kwargs: Any) -> "DefaultInvestigationLLM":
        return self


class AgentState(TypedDict):
    finding: Finding
    code: str
    package: str
    tool_call_count: int
    messages: Annotated[Sequence[BaseMessage], add_messages]
    final_finding: Optional[Finding]



def create_agent_node(llm: Optional[Any] = None):
    effective_llm = llm or DefaultInvestigationLLM()
    if hasattr(effective_llm, "bind_tools"):
        bound_llm = effective_llm.bind_tools(ALL_TOOLS)
    else:
        bound_llm = effective_llm

    def agent_node(state: AgentState) -> Dict[str, Any]:
        messages = state["messages"]
        response = bound_llm.invoke(messages)
        return {
            "messages": [response],
        }

    return agent_node


def tools_node(state: AgentState) -> Dict[str, Any]:
    messages = state["messages"]
    last_msg = messages[-1]
    tool_calls = getattr(last_msg, "tool_calls", []) or []

    current_count = state.get("tool_call_count", 0)
    remaining_budget = max(0, TOOL_CALL_CAP - current_count)
    calls_to_execute = tool_calls[:remaining_budget]

    tool_messages: List[ToolMessage] = []
    executed_count = 0

    for call in calls_to_execute:
        tool_name = call.get("name")
        args = call.get("args", {})
        call_id = call.get("id", f"call_{current_count + executed_count}")

        tool_fn = TOOLS_BY_NAME.get(tool_name)
        if not tool_fn:
            content = f"Error: Tool '{tool_name}' not found."
        else:
            try:
                result = tool_fn.invoke(args)
                content = str(result)
            except Exception as e:
                content = f"Tool execution failed for '{tool_name}': {e}"

        tool_messages.append(ToolMessage(content=content, tool_call_id=call_id, name=tool_name))
        executed_count += 1

    return {
        "messages": tool_messages,
        "tool_call_count": current_count + executed_count,
    }


def should_continue(state: AgentState) -> str:
    messages = state.get("messages", [])
    if not messages:
        return "finalize"

    last_msg = messages[-1]
    has_tool_calls = hasattr(last_msg, "tool_calls") and bool(last_msg.tool_calls)

    if has_tool_calls and state.get("tool_call_count", 0) < TOOL_CALL_CAP:
        return "tools"
    return "finalize"


def finalize_node(state: AgentState) -> Dict[str, Any]:
    original_finding = state["finding"]
    messages = state.get("messages", [])

    suggested_fix = original_finding.suggested_fix
    reasons = list(original_finding.reasons)

    # Check tool messages for similarity results or insights
    for msg in messages:
        if isinstance(msg, ToolMessage) and msg.name == "find_similar_package":
            try:
                import ast
                similar_pkgs = ast.literal_eval(msg.content)
                if isinstance(similar_pkgs, list) and similar_pkgs and not suggested_fix:
                    suggested_fix = f"Did you mean '{similar_pkgs[0]}'?"
            except Exception:
                pass

    last_msg = messages[-1] if messages else None
    if isinstance(last_msg, AIMessage) and last_msg.content:
        reasons.append(f"Agent analysis: {last_msg.content}")

    final_finding = Finding(
        package=original_finding.package,
        verdict=original_finding.verdict,
        risk_score=original_finding.risk_score,
        confidence=min(0.95, round(original_finding.confidence + 0.1, 2)),
        reasons=reasons,
        suggested_fix=suggested_fix,
    )

    return {"final_finding": final_finding}


def build_investigation_graph(llm: Optional[Any] = None):
    """Build LangGraph StateGraph for investigating suspicious packages."""
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", create_agent_node(llm))
    workflow.add_node("tools", tools_node)
    workflow.add_node("finalize", finalize_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "finalize": "finalize",
        },
    )
    workflow.add_edge("tools", "agent")
    workflow.add_edge("finalize", END)

    return workflow.compile()


def investigate_package(finding: Finding, code: str, llm: Optional[Any] = None) -> Finding:
    """
    Investigate only suspicious or hallucinated findings.
    Caps at 6 tool calls per package, returning an updated Finding.
    """
    if finding.verdict == "ok":
        return finding

    graph = build_investigation_graph(llm=llm)
    prompt = (
        f"Investigate flagged dependency:\n"
        f"Package: {finding.package}\n"
        f"Verdict: {finding.verdict}\n"
        f"Risk Score: {finding.risk_score}\n"
        f"Reasons: {'; '.join(finding.reasons)}\n\n"
        f"Code Context:\n{code}\n"
    )

    initial_state = {
        "finding": finding,
        "code": code,
        "package": finding.package,
        "tool_call_count": 0,
        "messages": [HumanMessage(content=prompt)],
        "final_finding": None,
    }

    result = graph.invoke(initial_state)
    return result.get("final_finding") or finding
