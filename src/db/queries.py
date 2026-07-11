import sqlite3

from src.config import DB_PATH


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


def get_eligible_courses(
    district: str,
    z_score: float,
    year: str = "2024/2025",
) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
            co.uni_code,
            co.course_code_base,
            COALESCE(co.course_name, c.course_name, co.course_code_base) AS course_name,
            co.university,
            co.district,
            co.academic_year,
            co.z_score AS cutoff
        FROM cutoffs co
        LEFT JOIN courses c ON c.course_code_base = co.course_code_base
        WHERE UPPER(co.district) = UPPER(?)
          AND co.academic_year = ?
          AND co.nqc_flag = 0
          AND co.z_score IS NOT NULL
          AND co.z_score <= ?
        ORDER BY co.z_score DESC
        """,
        (district, year, z_score),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_gap_analysis(
    district: str,
    z_score: float,
    course_code: str,
    year: str = "2024/2025",
) -> dict:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
            co.uni_code,
            COALESCE(co.course_name, c.course_name, co.course_code_base) AS course_name,
            co.university,
            co.z_score AS cutoff,
            co.nqc_flag
        FROM cutoffs co
        LEFT JOIN courses c ON c.course_code_base = co.course_code_base
        WHERE UPPER(co.district) = UPPER(?)
          AND co.course_code_base = ?
          AND co.academic_year = ?
        ORDER BY co.z_score ASC
        """,
        (district, course_code, year),
    ).fetchall()
    conn.close()

    if not rows:
        return {
            "qualifies": False,
            "message": "No cutoff data for this course/district/year.",
        }

    qualifying = [
        dict(r) for r in rows if not r["nqc_flag"] and r["cutoff"] is not None
    ]
    if not qualifying:
        return {
            "qualifies": False,
            "message": "All entries are NQC for this district.",
        }

    best = min(qualifying, key=lambda r: r["cutoff"])
    gap = best["cutoff"] - z_score
    return {
        "course_code": course_code,
        "district": district,
        "your_z_score": z_score,
        "lowest_cutoff": best["cutoff"],
        "university": best["university"],
        "uni_code": best["uni_code"],
        "gap": round(gap, 4),
        "qualifies": gap <= 0,
        "academic_year": year,
        "data_label": "official_cutoffs",
    }