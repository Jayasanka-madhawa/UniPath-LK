import json
from pathlib import Path

from src.rag.answer import answer_question

golden = json.loads(Path("eval/golden_qa.json").read_text())

passed = 0
for item in golden:
    answer = answer_question(item["question"])
    answer_lower = answer.lower()
    ok = all(term.lower() in answer_lower for term in item["must_contain"])
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {item['question']}")
    if not ok:
        print(f"       expected terms: {item['must_contain']}")
        print(f"       answer preview: {answer[:200]}...")
    else:
        passed += 1

print(f"\nScore: {passed}/{len(golden)}")
