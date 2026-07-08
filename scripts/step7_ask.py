import sys
from src.rag.answer import answer_question

question = " ".join(sys.argv[1:]).strip()
if not question:
    question = "What is the maximum number of A/L attempts allowed?"

print("Q:", question)
print("=" * 60)
print(answer_question(question))