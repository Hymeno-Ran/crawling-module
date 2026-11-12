"""Parse trang danh sách việc làm ITviec.

Không dựa vào class CSS (hay đổi) mà dựa vào mẫu link:
  - link tin tuyển dụng: /it-jobs/<slug>-<số>
  - link công ty:        /companies/<slug>
  - tag kỹ năng:         /it-jobs/<skill>?click_source=Skill tag
Nếu ITviec đổi giao diện và parse ra 0 job, crawler sẽ thoát với mã lỗi.
"""
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

BASE_URL = "https://itviec.com"
JOB_PATH = re.compile(r"^/it-jobs/([a-z0-9-]+-\d+)/?$")
COMPANY_PATH = re.compile(r"^/companies/[a-z0-9-]+/?$")
POSTED = re.compile(r"Posted\s+(.+?\bago)", re.I)
WORK_MODES = ("At office", "Hybrid", "Remote")
CITIES = ("Ha Noi", "Ho Chi Minh", "Da Nang", "Others")


@dataclass
class Job:
    slug: str
    title: str
    url: str
    company: str | None = None
    location: str | None = None
    work_mode: str | None = None
    skills: list[str] = field(default_factory=list)
    posted_text: str | None = None


def _path(href: str) -> str:
    return urlparse(urljoin(BASE_URL, href)).path


def _find_card(link: Tag) -> Tag:
    """Đi ngược lên cây DOM tới phần tử nhỏ nhất chứa cả link công ty."""
    node = link
    while node.parent is not None and node.parent.name != "[document]":
        node = node.parent
        if node.find("a", href=lambda h: h and COMPANY_PATH.match(_path(h))):
            return node
    return link.parent


def parse_listing(html: str) -> list[Job]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: dict[str, Job] = {}

    for a in soup.find_all("a", href=True):
        m = JOB_PATH.match(_path(a["href"]))
        title = a.get_text(" ", strip=True)
        if not m or not title:
            continue
        slug = m.group(1)
        if slug in jobs:
            continue

        card = _find_card(a)
        text = card.get_text(" ", strip=True)
        company = None
        for c in card.find_all("a", href=True):
            if COMPANY_PATH.match(_path(c["href"])) and c.get_text(strip=True):
                company = c.get_text(" ", strip=True)
                break
        skills = sorted({
            s.get_text(strip=True)
            for s in card.find_all("a", href=True)
            if "click_source=Skill" in s["href"] and s.get_text(strip=True)
        })
        posted = POSTED.search(text)
        location = next(
            (seg for seg in re.split(r"\s{2,}|\n", card.get_text("\n", strip=True))
             if any(seg.startswith(city) for city in CITIES)),
            None,
        )
        jobs[slug] = Job(
            slug=slug,
            title=title,
            url=f"{BASE_URL}/it-jobs/{slug}",
            company=company,
            location=location,
            work_mode=next((w for w in WORK_MODES if w in text), None),
            skills=skills,
            posted_text=posted.group(1) if posted else None,
        )
    return list(jobs.values())
