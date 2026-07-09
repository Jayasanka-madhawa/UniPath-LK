from langchain_core.tools import tool

from src.agent.tools_rag import lookup_section_tool, search_handbook_tool
from src.agent.tools_structured import (
    compare_courses_tool,
    find_course_tool,
    get_eligible_courses_tool,
    get_gap_analysis_tool,
)


@tool
def compare_courses(course_1: str, course_2: str) -> str:
    """Compare two UGC courses (intake, universities, eligibility).
    Use full names like 'Physical Science' or codes like '013'."""
    return compare_courses_tool(course_1, course_2)


@tool
def find_course(name: str) -> str:
    """Look up a course catalogue record by name."""
    return find_course_tool(name)


@tool
def get_eligible_courses(district: str, z_score: float, year: str = "2024/2025") -> str:
    """List courses/universities a student qualifies for at a district and Z-score."""
    return get_eligible_courses_tool(district, z_score, year)


@tool
def get_gap_analysis(
    district: str, z_score: float, course_code: str, year: str = "2024/2025"
) -> str:
    """Gap analysis: how far a student is from qualifying for a course in a district."""
    return get_gap_analysis_tool(district, z_score, course_code, year)


@tool
def search_handbook(query: str) -> str:
    """Search UGC handbook policy/procedure text (SLIATE, appeals, Uni-Code)."""
    return search_handbook_tool(query)


@tool
def lookup_section(section_id: str) -> str:
    """Fetch handbook content for a section number such as '1.7' or '3.3'."""
    return lookup_section_tool(section_id)


ALL_TOOLS = [
    compare_courses,
    find_course,
    get_eligible_courses,
    get_gap_analysis,
    search_handbook,
    lookup_section,
]
