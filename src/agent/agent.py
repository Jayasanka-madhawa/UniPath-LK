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


def _error_result(messages: list[dict[str, str]], error: str) -> AgentResult:
    return AgentResult(
        question=_last_user_message(messages),
        answer=(
            "Sorry, I ran into a problem answering that.\n\n"
            f"**Details:** {error}\n\n"
            "Try:\n"
            "- Confirm Ollama is running (`ollama list`)\n"
            "- Restart the app: stop Streamlit and run `streamlit run app.py` again\n"
            "- Run from the project folder with `export PYTHONPATH=.`"
        ),
        tool_calls=[],
        backend="error",
    )


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
    use_legacy: bool = False,
) -> AgentResult:
    """Run agent via LangGraph with optional conversation history."""
    if messages is None:
        messages = [{"role": "user", "content": question or ""}]
    elif question is not None:
        messages = [*messages, {"role": "user", "content": question}]

    if use_legacy:
        return run_legacy_agent(
            _last_user_message(messages),
            max_steps=max_steps,
            history=messages[:-1],
        )

    try:
        return _run_langgraph_agent(messages)
    except ImportError as exc:
        return _error_result(
            messages,
            f"LangGraph dependencies missing ({exc}). Run: pip install -r requirements.txt",
        )
    except Exception as exc:
        return _error_result(messages, str(exc))


__all__ = ["AgentResult", "ToolCall", "run_agent"]
