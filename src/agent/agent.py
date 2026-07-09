from src.agent.legacy import AgentResult, ToolCall, run_legacy_agent


def _extract_tool_calls(messages: list) -> list[ToolCall]:
    tool_calls: list[ToolCall] = []
    pending: dict[str, dict] = {}

    for msg in messages:
        msg_type = getattr(msg, "type", None)
        if msg_type == "ai" and getattr(msg, "tool_calls", None):
            for call in msg.tool_calls:
                pending[call["id"]] = {
                    "action": call["name"],
                    "args": call.get("args") or {},
                }
        elif msg_type == "tool":
            info = pending.get(getattr(msg, "tool_call_id", ""), {})
            tool_calls.append(
                ToolCall(
                    action=info.get("action", getattr(msg, "name", "tool")),
                    args=info.get("args", {}),
                    observation=str(msg.content),
                )
            )
    return tool_calls


def _run_langgraph_agent(question: str) -> AgentResult:
    from src.agent.graph import run_graph

    result = run_graph(question)
    messages = result["messages"]
    answer = messages[-1].content if messages else "No response."
    return AgentResult(
        question=question,
        answer=answer,
        tool_calls=_extract_tool_calls(messages),
        backend="langgraph",
    )


def run_agent(question: str, max_steps: int = 4) -> AgentResult:
    """Run agent via LangGraph if available, else legacy Ollama JSON loop."""
    try:
        return _run_langgraph_agent(question)
    except ImportError:
        return run_legacy_agent(question, max_steps=max_steps)
    except Exception:
        return run_legacy_agent(question, max_steps=max_steps)


__all__ = ["AgentResult", "ToolCall", "run_agent"]
