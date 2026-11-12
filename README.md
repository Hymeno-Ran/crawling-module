# devops-lab — crawler việc làm DevOps Hà Nội

App mẫu cho chuỗi lab DevOps. Hai service dùng chung một Postgres:

| Service | Chạy kiểu | Lệnh | Sau này deploy thành |
| --- | --- | --- | --- |
| `crawler` | chạy 1 lần rồi thoát | `python -m app.crawler.main --pages 2` | ECS scheduled task / K8s CronJob |
| `api` | web server, cổng 8080 | `uvicorn app.api.main:app --host 0.0.0.0 --port 8080` | ECS service / K8s Deployment |

Nguồn: `https://itviec.com/it-jobs/devops/ha-noi` (robots.txt cho phép, đã kiểm tra 04/11/2026).
Crawler đọc robots.txt trước mỗi trang, nghỉ 3 giây giữa các trang, tối đa vài trang. Chỉ dùng để học, đừng chạy dày.

## Chạy trên máy (chưa có Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt
pytest -q                                                      # 9 test, không cần DB/mạng
python -m app.crawler.main --fixture tests/fixtures/listing.html --dry-run   # parse thử, không mạng
python -m app.crawler.main --pages 1 --dry-run                 # crawl thật, in ra, không ghi DB
```

Cần Postgres để ghi dữ liệu: đặt biến `PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE` (xem `.env.example`).
Bảng `jobs` được tạo bởi `db/init.sql` (mount vào `/docker-entrypoint-initdb.d/` của container postgres) và crawler cũng tự tạo nếu chưa có.

## API

| Endpoint | Ý nghĩa |
| --- | --- |
| `GET /healthz` | process còn sống (không chạm DB) → dùng cho liveness |
| `GET /readyz` | kết nối được DB → 200, không → 503 → dùng cho readiness |
| `GET /jobs?skill=aws&keyword=senior&limit=50` | danh sách job; `skill` khớp đúng một kỹ năng, `keyword` tìm trong tiêu đề, công ty, địa điểm, kỹ năng (không phân biệt hoa thường, có phân biệt dấu) |
| `GET /stats/skills` | top kỹ năng trong tin DevOps Hà Nội |

## Lưu ý

- Parser dựa vào mẫu link (`/it-jobs/<slug>-<số>`, `/companies/...`, `click_source=Skill`), không dựa vào class CSS.
  Fixture trong `tests/fixtures/` là bản rút gọn mô phỏng, không phải HTML gốc. Lần chạy thật đầu tiên hãy kiểm tra
  kết quả `--dry-run`; nếu company/location sai hoặc ra 0 job thì lưu HTML thật làm fixture và sửa `parser.py`.
- Crawler thoát mã 1 khi parse ra 0 job → dùng làm tín hiệu alert ở lab monitoring.
- Dockerfile, compose, pipeline, manifest K8s là phần bạn tự viết trong các lab.
