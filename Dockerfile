# Build resource stage: chỉ để cài thư viện, không nằm trong image cuối
FROM python:3.12-slim AS resource-app

WORKDIR /build

COPY requirements/ ./requirements/

RUN pip install --prefix=/install -r requirements/crawler.txt

FROM python:3.12-slim AS resource-api

WORKDIR /build

COPY requirements/ ./requirements/

RUN pip install --prefix=/install -r requirements/api.txt


# Runtime stage: image sạch, dùng chung cho cả 2 service
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN useradd --no-create-home --uid 10001 app

# run stage
FROM runner AS app

WORKDIR /app

COPY --from=resource-app /install /usr/local
COPY app/ ./app/
USER app
ENTRYPOINT ["python", "-m", "app.crawler.main" ]
CMD ["--pages","2"]

FROM runner AS api

WORKDIR /app
COPY --from=resource-api /install /usr/local
COPY app/ ./app/
USER app
HEALTHCHECK --interval=30s --timeout=3s \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz', timeout=2)"]
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8080"]