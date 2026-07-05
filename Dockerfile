FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 1000 --create-home --shell /usr/sbin/nologin app

COPY --from=builder /install /usr/local
COPY . .

# Environment variable to switch DB, defaults to SQLite if not provided
ENV DATABASE_URL=sqlite:////app/data/precios.db
ENV GUNICORN_WORKERS=2
ENV GUNICORN_TIMEOUT=60

USER app

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/v1/health')" || exit 1

CMD exec gunicorn -b 0.0.0.0:5000 -w ${GUNICORN_WORKERS} -t ${GUNICORN_TIMEOUT} app:app
