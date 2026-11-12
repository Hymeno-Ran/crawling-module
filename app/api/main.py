"""API đọc kết quả crawl.

    uvicorn app.api.main:app --host 0.0.0.0 --port 8080
"""
from fastapi import FastAPI, HTTPException, Query
from psycopg.rows import dict_row

from app.common import db

app = FastAPI(title="devops-jobs-api")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    try:
        with db.connect() as conn:
            conn.execute("SELECT 1")
    except Exception:
        raise HTTPException(status_code=503, detail="db not ready")
    return {"status": "ready"}


@app.get("/jobs")
def list_jobs(skill: str | None = None, keyword: str | None = None,
              limit: int = Query(50, le=200)):
    sql = ("SELECT slug, title, company, location, work_mode, skills, "
           "posted_text, url, last_seen FROM jobs")
    conditions: list[str] = []
    params: list = []
    if skill:
        conditions.append("EXISTS (SELECT 1 FROM unnest(skills) s WHERE lower(s) = lower(%s))")
        params.append(skill)
    keyword = keyword.strip() if keyword else ""
    if keyword:
        # Escape để % và _ trong từ khóa được hiểu là ký tự thường, không phải wildcard
        escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        conditions.append("(title ILIKE %s OR company ILIKE %s OR location ILIKE %s "
                          "OR array_to_string(skills, ' ') ILIKE %s)")
        params += [f"%{escaped}%"] * 4
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY last_seen DESC LIMIT %s"
    params.append(limit)
    with db.connect() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


@app.get("/stats/skills")
def skill_stats():
    """Kỹ năng nào xuất hiện nhiều nhất trong tin DevOps Hà Nội."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT s AS skill, count(*) AS jobs FROM jobs, unnest(skills) s "
            "GROUP BY s ORDER BY jobs DESC, s LIMIT 20"
        ).fetchall()
    return [{"skill": s, "jobs": n} for s, n in rows]
