FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app
ENV ORCAST_ENV=production
ENV ORCAST_STORAGE_BACKEND=aws
ENV PORT=8080

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY archive/public-templates-backup-20250720/api/verified-sightings.json ./archive/public-templates-backup-20250720/api/verified-sightings.json
COPY src/integrations/orcasound_hydrophones_for_orcast.json ./src/integrations/orcasound_hydrophones_for_orcast.json

EXPOSE 8080

CMD ["sh", "-c", "uvicorn src.aws_backend.main:app --host 0.0.0.0 --port ${PORT}"]

