import json
import re
from dataclasses import dataclass, field

import ollama

from src.agent.tools_rag import lookup_section_tool, search_handbook_tool
from src.agent.tools_structured import (
    compare_courses_tool,
    find_course_tool,
    get_eligible_courses_tool,
    get_gap_analysis_tool,
)
from src.config import CHAT_MODEL

AGENT_SYSTEM_PROMPT = """
You are UniPath LK, a UGC Sri Lanka admission agent.

Respond with ONLY one JSON object per turn.

Tools:
- compare_courses_tool(course_code_1, course_code_2)
- find_course_tool(name)
- get_eligible_courses_tool(district, z_score, year)
- get_gap_analysis_tool(district, z_score, course_code, year)
- search_handbook_tool(query)
- lookup_section_tool(section_id)
- final_answer(answer)

Rules:
- Use structured tools for course comparison, eligibility, and gap analysis.
- Use RAG tools for policy/process questions.
- Never invent Z-scores or cutoffs.
- Include handbook citations when using RAG.
- For compare questions pass full course names or 3-digit codes like "013", never abbreviations.
"""

TOOL_MAP = {
    "compare_courses_tool": compare_courses_tool,
    "find_course_tool": find_course_tool,
    "get_eligible_courses_tool": get_eligible_courses_tool,
    "get_gap_analysis_tool": get_gap_analysis_tool,
    "search_handbook_tool": search_handbook_tool,
    "lookup_section_tool": lookup_section_tool,
}


@dataclass
class ToolCall:
    action: str
    args: dict
    observation: str


@dataclass
class AgentResult:
    question: str
    answer: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    backend: str = "legacy"


def _synthesize_final_answer(question: str, tool_calls: list[ToolCall]) -> str:
    if not tool_calls:
        return "I don't have enough information to answer this."

    observations = "\n\n---\n\n".join(
        f"Tool: {c.action}({json.dumps(c.args)})\n{c.observation}"
        for c in tool_calls
    )

    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Write the final answer using ONLY the tool observations below. "
                    "Include citations when from handbook. "
                    "If observations lack the answer, say you don't have enough information."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nObservations:\n{observations}",
            },
        ],
        options={"temperature": 0},
    )
    return response["message"]["content"]


def _parse_json(content: str) -> dict | None:
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, flags=re.DOTALL)
    if fence:
        content = fence.group(1)
    start, end = content.find("{"), content.rfind("}")
    if start == -1:
        return None
    try:
        return json.loads(content[start : end + 1])
    except json.JSONDecodeError:
        return None


def run_legacy_agent(question: str, max_steps: int = 4) -> AgentResult:
    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    tool_calls: list[ToolCall] = []

    for _ in range(max_steps):
        response = ollama.chat(
            model=CHAT_MODEL,
            messages=messages,
            options={"temperature": 0},
        )["message"]["content"]

        parsed = _parse_json(response)
        if not parsed:
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": "Reply with valid JSON only."})
            continue

        action = parsed.get("action", "")
        args = parsed.get("args") or {}

        if action == "final_answer":
            if tool_calls:
                answer = _synthesize_final_answer(question, tool_calls)
            else:
                answer = args.get("answer", "").strip()
                if not answer:
                    answer = "I don't have enough information to answer this."
            return AgentResult(
                question=question,
                answer=answer,
                tool_calls=tool_calls,
                backend="legacy",
            )

        if action not in TOOL_MAP:
            observation = f"Unknown tool: {action}"
        else:
            observation = TOOL_MAP[action](**args)

        tool_calls.append(ToolCall(action=action, args=args, observation=observation))
        messages.append({"role": "assistant", "content": json.dumps(parsed)})
        messages.append({"role": "user", "content": f"Observation:\n{observation}"})

    return AgentResult(
        question=question,
        answer=_synthesize_final_answer(question, tool_calls),
        tool_calls=tool_calls,
        backend="legacy",
    )
