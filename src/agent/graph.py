from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from src.agent.langchain_tools import ALL_TOOLS
from src.config import CHAT_MODEL

SYSTEM_PROMPT = """You are UniPath LK, a friendly UGC Sri Lanka university admission assistant.

You help students with:
- Course eligibility, Z-scores, and cutoffs
- Comparing degree programmes and universities
- UGC handbook rules and procedures (applications, Uni-Code, SLIATE, appeals)

Conversation:
- Be warm and clear. Handle greetings naturally and offer to help.
- Use earlier messages for context (district, Z-score, course names mentioned before).
- Ask a short clarifying question when required info is missing (e.g. district before eligibility).
- Stay focused on UGC/university admission. Politely redirect off-topic questions.
- Never mention internal tools, RAG, agents, or databases to the user.

Tools (use silently when needed):
- get_eligible_courses / get_gap_analysis / compare_courses / find_course for course and cutoff facts
- search_handbook / lookup_section for policy and process questions

Rules:
- Never invent Z-scores or cutoffs; only report tool output.
- If a tool returns "Found N eligible", report that count and summarize — do not say none unless the tool says so.
- For handbook answers include citation: (Section X.X, Handbook 2025/26, p.N)
- Label structured data as official catalogue/cutoff data (2024/2025).
- If tools lack information, say you don't have enough information.
"""

_agent = None


def build_agent():
    global _agent
    if _agent is None:
        llm = ChatOllama(model=CHAT_MODEL, temperature=0)
        _agent = create_react_agent(
            llm,
            ALL_TOOLS,
            prompt=SystemMessage(content=SYSTEM_PROMPT),
        )
    return _agent


def to_langchain_messages(history: list[dict[str, str]]) -> list[BaseMessage]:
    messages: list[BaseMessage] = []
    for item in history:
        role = item.get("role", "")
        content = item.get("content", "")
        if not content:
            continue
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


def run_graph(messages: list[BaseMessage] | list[dict[str, str]]) -> dict:
    agent = build_agent()
    if messages and isinstance(messages[0], dict):
        messages = to_langchain_messages(messages)
    return agent.invoke({"messages": messages})
