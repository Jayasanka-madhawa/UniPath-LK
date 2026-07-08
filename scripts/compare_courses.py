import sys

from src.db.queries import compare_courses, find_course_by_name


def resolve_code(value: str) -> str:
    value = value.strip()
    if value.isdigit():
        return value.zfill(3) if len(value) <= 3 else value

    course = find_course_by_name(value)
    if not course:
        raise ValueError(f"Could not find course: {value}")
    return course["course_code_base"]


def print_course(label: str, course: dict) -> None:
    print(f"\n{label}: {course['course_name']} ({course['course_code_base']})")
    print(f"  Intake: {course['proposed_intake']}")
    print(f"  Universities ({len(course['available_universities'])}):")
    for uni in course["available_universities"]:
        print(f"    - {uni}")
    print(f"  Duration: {course['duration'] or 'N/A'}")
    print(f"  Medium: {course['medium'] or 'N/A'}")
    if course["eligibility_text"]:
        preview = course["eligibility_text"][:220]
        print(f"  Eligibility: {preview}...")


def main() -> None:
    if len(sys.argv) < 3:
        print('Usage: python scripts/compare_courses.py "Physical Science" "Computer Science"')
        print('   or: python scripts/compare_courses.py 013 012')
        sys.exit(1)

    code1 = resolve_code(sys.argv[1])
    code2 = resolve_code(sys.argv[2])
    result = compare_courses(code1, code2)

    print("=" * 60)
    print("COURSE COMPARISON")
    print("=" * 60)
    print_course("Course A", result["course_a"])
    print_course("Course B", result["course_b"])

    comp = result["comparison"]
    print("\nSummary")
    print(f"  Intake difference (A - B): {comp['intake_difference']}")
    print(f"  University count A: {comp['university_count_a']}")
    print(f"  University count B: {comp['university_count_b']}")
    print(f"  Source: {result['data_label']}")


if __name__ == "__main__":
    main()