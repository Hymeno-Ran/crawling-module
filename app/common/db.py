"""Kết nối Postgres. Cấu hình qua biến môi trường chuẩn của libpq:
PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE (hoặc DATABASE_URL)."""
import os

import psycopg

SCHEMA = """
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
"""


def connect() -> psycopg.Connection:
    # Chuỗi rỗng => psycopg tự đọc các biến PG* từ môi trường
    return psycopg.connect(os.getenv("DATABASE_URL", ""), connect_timeout=3)


def init_schema(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(SCHEMA)
    conn.commit()
