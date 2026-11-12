-- Postgres chạy file này lần đầu khi mount vào /docker-entrypoint-initdb.d/
CREATE TABLE IF NOT EXISTS jobs (
    slug        TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    company     TEXT,
    location    TEXT,
    work_mode   TEXT,
    skills      TEXT[] NOT NULL DEFAULT '{}',
    posted_text TEXT,
    url         TEXT NOT NULL,
    first_seen  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen   TIMESTAMPTZ NOT NULL DEFAULT now()
);
