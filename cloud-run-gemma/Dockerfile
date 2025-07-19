# ORCAST Gemma 3 Cloud Run GPU Service
# For Google Cloud Hackathon - Agentic AI on Cloud Run GPUs

FROM nvidia/cuda:12.1-runtime-ubuntu22.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app
ENV MODEL_NAME=google/gemma-2-2b-it

# Download and cache model (optional - can be done at runtime)
# RUN python3 download_model.py

# Run the application
CMD ["python3", "main.py"] 