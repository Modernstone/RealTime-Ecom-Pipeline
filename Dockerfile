# =============================================================================
# Real-Time E-Commerce Data Pipeline - Multi-stage Docker Build
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Builder - install dependencies
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system dependencies required for building Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: Runtime - minimal production image
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

LABEL maintainer="data-engineering-team"
LABEL version="1.0.0"
LABEL description="Real-Time E-Commerce Data Pipeline & Analytics Platform"
LABEL org.opencontainers.image.source="https://github.com/org/ecommerce-pipeline"

# Install only the runtime library for PostgreSQL
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN groupadd --gid 1000 pipeline && \
    useradd --uid 1000 --gid pipeline --shell /bin/bash --create-home pipeline

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source code
COPY src/ ./src/
COPY config/ ./config/
COPY dashboard/ ./dashboard/

# Create directories for data and logs with proper ownership
RUN mkdir -p /app/data/raw /app/data/processed /app/logs && \
    chown -R pipeline:pipeline /app

# Set Python path so modules are importable
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER pipeline

# Healthcheck - verify the pipeline process is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command: run the pipeline
CMD ["python", "src/pipeline.py"]
