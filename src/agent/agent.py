from src.agent.legacy import AgentResult, ToolCall, run_legacy_agent


def _extract_tool_calls(messages: list, since: int = 0) -> list[ToolCall]:
    tool_calls: list[ToolCall] = []
    pending: dict[str, dict] = {}

    for msg in messages[since:]:
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


def _last_user_message(messages: list[dict[str, str]]) -> str:
    for item in reversed(messages):
        if item.get("role") == "user":
            return item.get("content", "")
    return ""


def _run_langgraph_agent(messages: list[dict[str, str]]) -> AgentResult:
    from src.agent.graph import run_graph, to_langchain_messages

    lc_messages = to_langchain_messages(messages)
    before_count = len(lc_messages)
    result = run_graph(lc_messages)
    all_messages = result["messages"]
    answer = all_messages[-1].content if all_messages else "No response."
    return AgentResult(
        question=_last_user_message(messages),
        answer=answer,
        tool_calls=_extract_tool_calls(all_messages, since=before_count),
        backend="langgraph",
    )


def run_agent(
    question: str | None = None,
    *,
    messages: list[dict[str, str]] | None = None,
    max_steps: int = 4,
) -> AgentResult:
    """Run agent via LangGraph with optional conversation history."""
    if messages is None:
        messages = [{"role": "user", "content": question or ""}]
    elif question is not None:
        messages = [*messages, {"role": "user", "content": question}]

    try:
        return _run_langgraph_agent(messages)
    except ImportError:
        return run_legacy_agent(
            _last_user_message(messages),
            max_steps=max_steps,
            history=messages[:-1],
        )
    except Exception:
        return run_legacy_agent(
            _last_user_message(messages),
            max_steps=max_steps,
            history=messages[:-1],
        )


__all__ = ["AgentResult", "ToolCall", "run_agent"]
