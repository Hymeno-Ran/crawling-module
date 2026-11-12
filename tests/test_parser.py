from pathlib import Path

from app.crawler.parser import parse_listing

FIXTURE = Path(__file__).parent / "fixtures" / "listing.html"


def test_parse_two_jobs():
    jobs = parse_listing(FIXTURE.read_text(encoding="utf-8"))
    assert [j.slug for j in jobs] == [
        "senior-devops-engineer-vinsmart-future-3151",
        "devops-engineer-khoi-cong-nghe-thong-tin-mb-bank-2109",
    ]


def test_fields_of_first_job():
    job = parse_listing(FIXTURE.read_text(encoding="utf-8"))[0]
    assert job.title == "Senior DevOps Engineer"
    assert job.company == "VinSmart Future"
    assert job.location == "Ha Noi - Ho Chi Minh"
    assert job.work_mode == "At office"
    assert job.posted_text == "2 days ago"
    assert job.skills == ["AWS", "Azure", "DevOps"]
    assert job.url == "https://itviec.com/it-jobs/senior-devops-engineer-vinsmart-future-3151"


def test_role_link_is_not_a_job():
    # /it-jobs/devops-engineer (không có số ở cuối) là link vai trò, không phải tin tuyển dụng
    slugs = [j.slug for j in parse_listing(FIXTURE.read_text(encoding="utf-8"))]
    assert "devops-engineer" not in slugs


def test_empty_page():
    assert parse_listing("<html><body>Không có job</body></html>") == []
