CREATE TABLE IF NOT EXISTS courses (
    course_code_base TEXT PRIMARY KEY,
    course_name TEXT NOT NULL,
    section TEXT,
    degree_programme TEXT,
    eligibility_text TEXT,
    duration TEXT,
    medium TEXT,
    proposed_intake INTEGER
);

CREATE TABLE IF NOT EXISTS course_universities (
    course_code_base TEXT NOT NULL,
    university TEXT NOT NULL,
    PRIMARY KEY (course_code_base, university),
    FOREIGN KEY (course_code_base) REFERENCES courses(course_code_base)
);