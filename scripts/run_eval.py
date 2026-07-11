import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.db.queries import (
    compare_courses,
    find_course_by_name,
    get_eligible_courses,
    get_gap_analysis,
)
from src.config import LLM_PROVIDER
from src.rag.answer import answer_question


def load_json(name: str) -> list:
    return json.loads((ROOT / "eval" / name).read_text())


def run_policy_eval() -> tuple[int, int]:
    golden = load_json("golden_qa_policy.json")
    passed = 0
    print("=== Policy (RAG) ===")
    print(f"(LLM provider: {LLM_PROVIDER})")
    for item in golden:
        answer = answer_question(item["question"], provider=LLM_PROVIDER)
        answer_lower = answer.lower()
        ok = all(term.lower() in answer_lower for term in item["must_contain"])
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {item['question']}")
        if not ok:
            print(f"       expected: {item['must_contain']}")
            print(f"       preview: {answer[:200]}...")
        else:
            passed += 1
    return passed, len(golden)


def _check_structured(item: dict) -> tuple[bool, str]:
    t = item["type"]
    args = item["args"]
    expect = item["expect"]

    if t == "find_course":
        result = find_course_by_name(args["name"])
        if not result:
            return False, "course not found"
        for key, val in expect.items():
            if result.get(key) != val:
                return False, f"expected {key}={val}, got {result.get(key)}"
        return True, ""

    if t == "compare":
        result = compare_courses(args["course_1"], args["course_2"])
        if expect.get("has_comparison") and "comparison" not in result:
            return False, "missing comparison"
        return True, ""

    if t == "eligible":
        rows = get_eligible_courses(args["district"], args["z_score"], args["year"])
        if len(rows) < expect.get("min_count", 0):
            return False, f"count {len(rows)} < {expect['min_count']}"
        code = expect.get("includes_code")
        if code and not any(r["course_code_base"] == code for r in rows):
            return False, f"missing course code {code}"
        return True, ""

    if t == "gap":
        result = get_gap_analysis(
            args["district"], args["z_score"], args["course_code"], args["year"]
        )
        if result.get("qualifies") != expect.get("qualifies"):
            return False, f"qualifies={result.get('qualifies')}"
        return True, ""

    return False, f"unknown type {t}"


def run_structured_eval() -> tuple[int, int]:
    golden = load_json("golden_qa_structured.json")
    passed = 0
    print("\n=== Structured (SQLite) ===")
    for item in golden:
        ok, reason = _check_structured(item)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {item['name']}")
        if not ok:
            print(f"       {reason}")
        else:
            passed += 1
    return passed, len(golden)


def main() -> None:
    policy_pass, policy_total = run_policy_eval()
    struct_pass, struct_total = run_structured_eval()
    total_pass = policy_pass + struct_pass
    total = policy_total + struct_total
    print(f"\nPolicy:     {policy_pass}/{policy_total}")
    print(f"Structured: {struct_pass}/{struct_total}")
    print(f"Total:      {total_pass}/{total}")


if __name__ == "__main__":
    main()
