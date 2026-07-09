from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from src.agent.langchain_tools import ALL_TOOLS
from src.config import CHAT_MODEL

SYSTEM_PROMPT = """You are UniPath LK, a UGC Sri Lanka university admission assistant.

Rules:
- Use get_eligible_courses / get_gap_analysis / compare_courses / find_course for numeric and catalogue facts.
- Use search_handbook / lookup_section for policy and process questions.
- Never invent Z-scores or cutoffs; only report tool output.
- If a tool returns a list or "Found N eligible", report that count and summarize options — do not say none unless the tool explicitly says so.
- For handbook answers include citation: (Section X.X, Handbook 2025/26, p.N)
- Label structured data as official catalogue/cutoff data (2024/2025).
- If tools lack information, say you don't have enough information.
"""


def build_agent():
    llm = ChatOllama(model=CHAT_MODEL, temperature=0)
    return create_react_agent(
        llm,
        ALL_TOOLS,
        prompt=SystemMessage(content=SYSTEM_PROMPT),
    )


def run_graph(question: str) -> dict:
    agent = build_agent()
    return agent.invoke({"messages": [("user", question)]})
