"""Crawler chạy một lần rồi thoát (hợp với ECS scheduled task / K8s CronJob).

    python -m app.crawler.main --pages 2
    python -m app.crawler.main --fixture tests/fixtures/listing.html   # không cần mạng
"""
import argparse
import logging
import sys
import time
import urllib.robotparser

import requests

from app.common import db
from app.crawler.parser import BASE_URL, Job, parse_listing

LISTING_URL = f"{BASE_URL}/it-jobs/devops/ha-noi"
USER_AGENT = "devops-lab-crawler/0.1 (hoc tap ca nhan)"
DELAY_SECONDS = 3

log = logging.getLogger("crawler")


def allowed_by_robots(session: requests.Session, url: str) -> bool:
    # Tải bằng session của crawler: rp.read() dùng User-Agent mặc định của urllib,
    # bị 403 thì RobotFileParser coi như cấm toàn bộ site
    resp = session.get(f"{BASE_URL}/robots.txt", timeout=15)
    resp.raise_for_status()
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(resp.text.splitlines())
    return rp.can_fetch(USER_AGENT, url)


def fetch_pages(pages: int) -> list[Job]:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    jobs: list[Job] = []
    for page in range(1, pages + 1):
        url = LISTING_URL if page == 1 else f"{LISTING_URL}?page={page}"
        if not allowed_by_robots(session, url):
            log.warning("robots.txt không cho phép %s, bỏ qua", url)
            continue
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        found = parse_listing(resp.text)
        log.info("trang %d: %d job", page, len(found))
        if not found:
            break
        jobs.extend(found)
        time.sleep(DELAY_SECONDS)  # lịch sự với site
    return jobs


def save(jobs: list[Job]) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        with conn.cursor() as cur:
            for j in jobs:
                cur.execute(
                    """
                    INSERT INTO jobs (slug, title, company, location, work_mode,
                                      skills, posted_text, url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (slug) DO UPDATE SET
                        title = EXCLUDED.title, company = EXCLUDED.company,
                        location = EXCLUDED.location, work_mode = EXCLUDED.work_mode,
                        skills = EXCLUDED.skills, posted_text = EXCLUDED.posted_text,
                        last_seen = now()
                    """,
                    (j.slug, j.title, j.company, j.location, j.work_mode,
                     j.skills, j.posted_text, j.url),
                )
        conn.commit()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=2)
    ap.add_argument("--fixture", help="đọc HTML từ file thay vì gọi mạng")
    ap.add_argument("--dry-run", action="store_true", help="chỉ in, không ghi DB")
    args = ap.parse_args()

    if args.fixture:
        with open(args.fixture, encoding="utf-8") as f:
            jobs = parse_listing(f.read())
    else:
        jobs = fetch_pages(args.pages)

    if not jobs:
        log.error("không parse được job nào — giao diện site có thể đã đổi")
        return 1
    if args.dry_run:
        for j in jobs:
            print(j)
    else:
        save(jobs)
    log.info("xong: %d job", len(jobs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
