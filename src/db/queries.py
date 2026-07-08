import sqlite3
from pathlib import Path

DB_PATH = Path("data/structured/unipath.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_course(row: sqlite3.Row, universities: list[str]) -> dict:
    return {
        "course_code_base": row["course_code_base"],
        "course_name": row["course_name"],
        "section": row["section"],
        "degree_programme": row["degree_programme"],
        "eligibility_text": row["eligibility_text"],
        "duration": row["duration"],
        "medium": row["medium"],
        "proposed_intake": row["proposed_intake"],
        "available_universities": universities,
    }


def get_course_details(course_code: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM courses WHERE course_code_base = ?",
        (course_code,),
    ).fetchone()

    if not row:
        conn.close()
        return None

    universities = [
        r["university"]
        for r in conn.execute(
            """
            SELECT university FROM course_universities
            WHERE course_code_base = ?
            ORDER BY university
            """,
            (course_code,),
        ).fetchall()
    ]
    conn.close()
    return _row_to_course(row, universities)


def find_course_by_name(name: str) -> dict | None:
    name = name.strip().lower()
    if not name:
        return None

    conn = get_connection()
    rows = conn.execute(
        "SELECT course_code_base, course_name FROM courses ORDER BY course_name"
    ).fetchall()
    conn.close()

    exact = [r for r in rows if r["course_name"].lower() == name]
    if exact:
        return get_course_details(exact[0]["course_code_base"])

    partial = [r for r in rows if name in r["course_name"].lower()]
    if len(partial) == 1:
        return get_course_details(partial[0]["course_code_base"])

    if len(partial) > 1:
        names = [r["course_name"] for r in partial[:5]]
        raise ValueError(f"Multiple matches for '{name}': {names}")

    return None


def compare_courses(course_code_1: str, course_code_2: str) -> dict:
    course_a = get_course_details(course_code_1)
    course_b = get_course_details(course_code_2)

    if not course_a:
        raise ValueError(f"Unknown course code: {course_code_1}")
    if not course_b:
        raise ValueError(f"Unknown course code: {course_code_2}")

    return {
        "course_a": course_a,
        "course_b": course_b,
        "comparison": {
            "intake_difference": (course_a["proposed_intake"] or 0)
            - (course_b["proposed_intake"] or 0),
            "university_count_a": len(course_a["available_universities"]),
            "university_count_b": len(course_b["available_universities"]),
        },
        "data_label": "official_catalogue",
    }