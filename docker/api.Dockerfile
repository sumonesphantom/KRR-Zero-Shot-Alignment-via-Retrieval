FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for better layer caching.
COPY requirements.txt /app/requirements.txt
COPY api/requirements-api.txt /app/api/requirements-api.txt

# Torch-cpu wheel keeps the image reasonable (~350MB vs ~3GB for CUDA).
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu torch==2.4.1 \
 && pip install -r /app/requirements.txt \
 && pip install -r /app/api/requirements-api.txt

# Copy source (see .dockerignore for exclusions).
COPY . /app

# Bake the FAISS index into the image. This downloads the MiniLM sentence
# encoder (~80MB) during build, which also pre-warms the embedder cache at
# runtime so first-request latency is just FAISS load, not a model download.
RUN python scripts/build_index.py

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -fs http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
