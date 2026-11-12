from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.api.main import app
from app.common import db

client = TestClient(app)


def fake_cursor(monkeypatch) -> MagicMock:
    conn = MagicMock()
    connect = MagicMock()
    connect.return_value.__enter__.return_value = conn
    monkeypatch.setattr(db, "connect", connect)
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = []
    return cur


def test_healthz_không_cần_db():
    assert client.get("/healthz").status_code == 200


def test_readyz_trả_503_khi_không_có_db(monkeypatch):
    monkeypatch.setenv("PGHOST", "127.0.0.1")
    monkeypatch.setenv("PGPORT", "1")  # cổng không có gì lắng nghe
    assert client.get("/readyz").status_code == 503


def test_jobs_kết_hợp_keyword_với_skill(monkeypatch):
    cur = fake_cursor(monkeypatch)
    assert client.get("/jobs", params={"skill": "docker", "keyword": " aws "}).status_code == 200
    sql, params = cur.execute.call_args.args
    assert ") AND (" in sql
    assert params == ["docker"] + ["%aws%"] * 4 + [50]


def test_jobs_escape_wildcard_trong_keyword(monkeypatch):
    cur = fake_cursor(monkeypatch)
    client.get("/jobs", params={"keyword": "100%_"})
    _, params = cur.execute.call_args.args
    assert params[0] == r"%100\%\_%"


def test_jobs_bỏ_qua_keyword_rỗng(monkeypatch):
    cur = fake_cursor(monkeypatch)
    client.get("/jobs", params={"keyword": "   "})
    sql, params = cur.execute.call_args.args
    assert "WHERE" not in sql
    assert params == [50]
