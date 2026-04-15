FROM python:3.11-slim AS builder

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && poetry install --no-dev --only=main

FROM python:3.11-slim\n\n# Install FFmpeg\nRUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

EXPOSE 8080

CMD ["uvicorn", "app.station_api:app", "--host", "0.0.0.0", "--port", "8080"]