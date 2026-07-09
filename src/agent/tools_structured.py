import json

from src.db.queries import (
    compare_courses,
    find_course_by_name,
    get_eligible_courses,
    get_gap_analysis,
)

def _resolve_code(value: str) -> str:
    value = value.strip()
    if value.isdigit():
        return value.zfill(3) if len(value) <= 3 else value
    course = find_course_by_name(value)
    if not course:
        raise ValueError(f"Could not find course: {value}")
    return course["course_code_base"]

def compare_courses_tool(course_code_1: str, course_code_2: str) -> str:
    try:
        result = compare_courses(_resolve_code(course_code_1), _resolve_code(course_code_2))
        return json.dumps(result, ensure_ascii=False, indent=2)
    except ValueError as exc:
        return str(exc)

def find_course_tool(name: str) -> str:
    try:
        course = find_course_by_name(name)
    except ValueError as exc:
        return str(exc)
    if not course:
        return f"No course found matching '{name}'."
    return json.dumps(course, ensure_ascii=False, indent=2)

def get_eligible_courses_tool(district: str, z_score: float, year: str = "2024/2025") -> str:
    results = get_eligible_courses(district, float(z_score), year)
    if not results:
        return f"No eligible courses for {district} at Z={z_score} ({year})."
    summary = (
        f"Found {len(results)} eligible university/course options for "
        f"{district} at Z={z_score} ({year}). Showing first 40:\n"
    )
    return summary + json.dumps(results[:40], ensure_ascii=False, indent=2)

def get_gap_analysis_tool(district: str, z_score: float, course_code: str, year: str = "2024/2025") -> str:
    try:
        code = _resolve_code(course_code)
    except ValueError as exc:
        return str(exc)
    return json.dumps(get_gap_analysis(district, float(z_score), code, year), ensure_ascii=False, indent=2)