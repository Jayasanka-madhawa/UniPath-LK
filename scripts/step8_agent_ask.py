import sys

from src.agent.agent import run_agent
from src.config import LLM_PROVIDER

question = " ".join(sys.argv[1:]).strip() or "Compare Physical Science vs Computer Science"
print("Q:", question)
print("Provider:", LLM_PROVIDER)
result = run_agent(question, llm_provider=LLM_PROVIDER)

for i, call in enumerate(result.tool_calls, 1):
    print(f"\n[Tool {i}] {call.action}({call.args})")
    print(call.observation[:600])

print(f"\nBackend: {result.backend}")
print("A:", result.answer)
