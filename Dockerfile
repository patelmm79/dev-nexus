# Multi-stage Docker build for Pattern Discovery Agent A2A Server
# Optimized for Cloud Run deployment

# ===================
# Stage 1: Builder
# ===================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies to user directory
RUN pip install --no-cache-dir --user -r requirements.txt

# ===================
# Stage 2: Runtime
# ===================
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY a2a/ ./a2a/
COPY core/ ./core/
COPY schemas/ ./schemas/
COPY config/ ./config/

# Set Python path to include user-installed packages
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# Expose Cloud Run default port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=3)"

# Run A2A server
CMD ["python", "-m", "uvicorn", "a2a.server:app", "--host", "0.0.0.0", "--port", "8080"]
