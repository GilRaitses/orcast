# Small amd64 python image for the bake-off mesh + fidelity steps.
# Build natively on the x86_64 EC2 host: docker build -f Dockerfile.py -t bakeoff-py .
FROM python:3.11-slim
RUN pip install --no-cache-dir \
    "numpy==1.26.4" \
    "rasterio==1.3.10"
WORKDIR /data
