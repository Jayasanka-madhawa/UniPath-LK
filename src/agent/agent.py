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


def _error_result(messages: list[dict[str, str]], error: str, provider: str | None = None) -> AgentResult:
    err_lower = error.lower()
    if "resource_exhausted" in err_lower or ("429" in error and "google" in (provider or "")):
        answer = (
            "Google Gemini **free-tier quota** is used up (or not available for this model).\n\n"
            "**What you can do now:**\n"
            "1. Switch sidebar to **OpenAI** or **Local (Ollama)**\n"
            "2. Wait about a minute and try Gemini again\n"
            "3. In `.env`, try `GOOGLE_MODEL=gemini-1.5-flash`\n"
            "4. Check usage: https://ai.dev/rate-limit\n\n"
            f"_Technical detail:_ {error[:400]}..."
        )
    elif "429" in error or "rate_limit" in err_lower or "quota" in err_lower:
        answer = (
            "The cloud API **rate limit or quota** was hit.\n\n"
            "**Try:** switch to another model in the sidebar (OpenAI / Ollama), "
            "wait a minute, or check your API billing dashboard.\n\n"
            f"_Technical detail:_ {error[:400]}..."
        )
    else:
        hints = [
            "- Run: `pip install -r requirements.txt`",
            "- Use **Local (Ollama)** if cloud API fails (`ollama serve`)",
            "- Set `OPENAI_API_KEY` or `GOOGLE_API_KEY` in `.env`",
            "- Restart Streamlit after changing `.env`",
        ]
        answer = (
            "Sorry, I ran into a problem answering that.\n\n"
            f"**Details:** {error}\n\n"
            "Try:\n"
            + "\n".join(hints)
        )
    return AgentResult(
        question=_last_user_message(messages),
        answer=answer,
        tool_calls=[],
        backend=f"error:{provider or 'unknown'}",
    )


def _run_langgraph_agent(
    messages: list[dict[str, str]],
    *,
    provider: str | None = None,
) -> AgentResult:
    from src.agent.graph import run_graph, to_langchain_messages
    from src.llm.chat import normalize_provider

    name = normalize_provider(provider)
    lc_messages = to_langchain_messages(messages)
    before_count = len(lc_messages)
    result = run_graph(lc_messages, provider=name)
    all_messages = result["messages"]
    answer = all_messages[-1].content if all_messages else "No response."
    return AgentResult(
        question=_last_user_message(messages),
        answer=answer,
        tool_calls=_extract_tool_calls(all_messages, since=before_count),
        backend=f"langgraph:{name}",
    )


def run_agent(
    question: str | None = None,
    *,
    messages: list[dict[str, str]] | None = None,
    max_steps: int = 4,
    use_legacy: bool = False,
    llm_provider: str | None = None,
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
        return _run_langgraph_agent(messages, provider=llm_provider)
    except ImportError as exc:
        return _error_result(
            messages,
            f"LangGraph dependencies missing ({exc}). Run: pip install -r requirements.txt",
            provider=llm_provider,
        )
    except Exception as exc:
        return _error_result(messages, str(exc), provider=llm_provider)


__all__ = ["AgentResult", "ToolCall", "run_agent"]
