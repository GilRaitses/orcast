# OrCast Behavioral ML Service Dockerfile
# For Cloud Run deployment with Python 3.12

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY cloud_run_service.py .
COPY behavioral_ml_service.py .
COPY hmc_sampling.py .
COPY redis_cache.py .

# Set environment variables
ENV PYTHONPATH=/app
ENV GOOGLE_CLOUD_PROJECT=orca-904de

# Expose port for Cloud Run
EXPOSE 8080

# Run the Cloud Run service
CMD ["python", "cloud_run_service.py"] 