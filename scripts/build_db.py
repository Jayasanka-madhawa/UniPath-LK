import json
import sqlite3
from pathlib import Path

SCHEMA_PATH = Path("src/db/schema.sql")
COURSES_PATH = Path("data/structured/courses.json")
DB_PATH = Path("data/structured/unipath.db")
CUTOFFS_PATH = Path("data/structured/cutoffs.json")


def parse_intake(value) -> int | None:
    if value is None:
        return None
    cleaned = str(value).replace(",", "").strip()
    if not cleaned.isdigit():
        return None
    return int(cleaned)


def load_courses() -> list[dict]:
    return json.loads(COURSES_PATH.read_text(encoding="utf-8"))

def load_cutoffs(conn: sqlite3.Connection) -> int:
    if not CUTOFFS_PATH.exists():
        print(f"No cutoffs file at {CUTOFFS_PATH} — skipping cutoffs")
        return 0

    cutoffs = json.loads(CUTOFFS_PATH.read_text(encoding="utf-8"))
    inserted = 0

    for row in cutoffs:
        conn.execute(
            """
            INSERT OR REPLACE INTO cutoffs (
                uni_code, course_code_base, course_name, university, district,
                stream, academic_year, z_score, nqc_flag
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["uni_code"],
                row["course_code_base"],
                row.get("course_name"),
                row["university"],
                row["district"],
                row.get("stream"),
                row["academic_year"],
                row.get("z_score"),
                1 if row.get("nqc_flag") else 0,
            ),
        )
        inserted += 1

    conn.commit()
    return inserted

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
    cutoff_count = load_cutoffs(conn)

    course_count = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    uni_count = conn.execute("SELECT COUNT(*) FROM course_universities").fetchone()[0]
    cutoff_total = conn.execute("SELECT COUNT(*) FROM cutoffs").fetchone()[0]
    conn.close()

    print(f"Database: {DB_PATH}")
    print(f"Courses inserted: {inserted_courses}")
    print(f"University rows inserted: {inserted_unis}")
    print(f"Skipped malformed rows: {skipped}")
    print(f"Cutoffs inserted: {cutoff_count}")
    print(f"Final counts -> courses: {course_count}, universities: {uni_count}, cutoffs: {cutoff_total}")


if __name__ == "__main__":
    build_db()