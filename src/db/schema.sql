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

CREATE TABLE IF NOT EXISTS cutoffs (
    uni_code TEXT NOT NULL,
    course_code_base TEXT NOT NULL,
    course_name TEXT,
    university TEXT,
    district TEXT NOT NULL,
    stream TEXT,
    academic_year TEXT NOT NULL,
    z_score REAL,
    nqc_flag INTEGER DEFAULT 0,
    PRIMARY KEY (uni_code, district, academic_year)
);