FROM python:3.11-slim

WORKDIR /app

COPY requirements_simple.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY orcast_production_backend.py .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "orcast_production_backend:app"] 