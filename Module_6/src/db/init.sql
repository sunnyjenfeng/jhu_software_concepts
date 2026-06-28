CREATE TABLE IF NOT EXISTS applicants (
    p_id SERIAL PRIMARY KEY,
    program TEXT,
    comments TEXT,
    date_added DATE,
    url TEXT UNIQUE, ---helps prevent duplicate applicant rows
    status TEXT,
    term TEXT,
    us_or_international TEXT,
    gpa FLOAT,
    gre FLOAT,
    gre_v FLOAT,
    gre_aw FLOAT,
    degree TEXT,
    llm_generated_program TEXT,
    llm_generated_university TEXT
);

-- ingestion_watermarks is a small tracking table.
-- Its job is to remember that a data source was loaded, when it was loaded, and how many rows were added.
-- CREATE TABLE IF NOT EXISTS ingestion_watermarks (
--     source_name TEXT PRIMARY KEY,
--     last_loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
--     rows_loaded INTEGER NOT NULL DEFAULT 0
-- );
CREATE TABLE IF NOT EXISTS ingestion_watermarks (
    source TEXT PRIMARY KEY,
    last_seen TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS analytics_results (
    query_number INTEGER PRIMARY KEY,
    question TEXT NOT NULL,
    columns JSONB NOT NULL,
    rows JSONB NOT NULL,
    error TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
