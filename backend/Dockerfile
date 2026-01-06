# ==============================================================================
# TcyberChatbot Backend Dockerfile
# Multi-stage build for FastAPI + ML dependencies
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Base image with system dependencies
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS base

# Install system dependencies required for ML libraries and file processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management via pip
RUN pip install --default-timeout=1000 uv

WORKDIR /app

# ------------------------------------------------------------------------------
# Stage 2: Install Python dependencies
# ------------------------------------------------------------------------------
FROM base AS deps

# Copy requirements files for layer caching
COPY requirements.txt requirements.docker.txt ./

# Prefer trimmed Docker requirements for faster, more reliable builds inside
# containerized environments. If `requirements.docker.txt` is present, install it;
# otherwise fall back to the full `requirements.txt`.
# Use uv for significantly faster installation
ENV UV_SYSTEM_PYTHON=1
ENV UV_HTTP_TIMEOUT=300
RUN if [ -s requirements.docker.txt ]; then \
    uv pip install --no-cache-dir -r requirements.docker.txt ; \
    else \
    uv pip install --no-cache-dir -r requirements.txt ; \
    fi

# ------------------------------------------------------------------------------
# Stage 3: Production image
# ------------------------------------------------------------------------------
FROM base AS production

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

WORKDIR /app

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs uploads data

# Create non-root user for security
RUN adduser --disabled-password --gecos '' --uid 1000 appuser \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
