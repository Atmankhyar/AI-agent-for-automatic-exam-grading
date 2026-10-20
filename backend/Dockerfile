FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-fra libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY worker ./worker
COPY alembic ./alembic
COPY alembic.ini .

RUN useradd --system --uid 10001 --home /app app \
    && mkdir -p /app/storage \
    && chown -R app /app/storage
USER app

ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
