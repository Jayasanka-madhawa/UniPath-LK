import json
import sqlite3
from pathlib import Path

SCHEMA_PATH = Path("src/db/schema.sql")
COURSES_PATH = Path("data/structured/courses.json")
DB_PATH = Path("data/structured/unipath.db")


def parse_intake(value) -> int | None:
    if value is None:
        return None
    cleaned = str(value).replace(",", "").strip()
    if not cleaned.isdigit():
        return None
    return int(cleaned)


def load_courses() -> list[dict]:
    return json.loads(COURSES_PATH.read_text(encoding="utf-8"))


def build_db() -> None:
    courses = load_courses()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    inserted_courses = 0
    inserted_unis = 0
    skipped = 0

    for course in courses:
        code = course.get("course_code_base")
        name = course.get("course_name")
        if not code or not name:
            skipped += 1
            continue

        conn.execute(
            """
            INSERT INTO courses (
                course_code_base, course_name, section, degree_programme,
                eligibility_text, duration, medium, proposed_intake
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                code,
                name,
                course.get("section"),
                course.get("degree_programme"),
                course.get("eligibility"),
                course.get("duration"),
                course.get("medium"),
                parse_intake(course.get("proposed_intake")),
            ),
        )
        inserted_courses += 1

        for university in course.get("available_universities") or []:
            uni = university.strip()
            if not uni:
                continue
            conn.execute(
                """
                INSERT OR IGNORE INTO course_universities (course_code_base, university)
                VALUES (?, ?)
                """,
                (code, uni),
            )
            inserted_unis += 1

    conn.commit()

    course_count = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    uni_count = conn.execute("SELECT COUNT(*) FROM course_universities").fetchone()[0]
    conn.close()

    print(f"Database: {DB_PATH}")
    print(f"Courses inserted: {inserted_courses}")
    print(f"University rows inserted: {inserted_unis}")
    print(f"Skipped malformed rows: {skipped}")
    print(f"Final counts -> courses: {course_count}, universities: {uni_count}")


if __name__ == "__main__":
    build_db()