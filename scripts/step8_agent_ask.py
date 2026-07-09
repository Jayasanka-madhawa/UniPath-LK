import sys
from src.agent.agent import run_agent

question = " ".join(sys.argv[1:]).strip() or "Compare Physical Science vs Computer Science"
print("Q:", question)
result = run_agent(question)

for i, call in enumerate(result.tool_calls, 1):
    print(f"\n[Tool {i}] {call.action}({call.args})")
    print(call.observation[:600])

print("\nA:", result.answer)