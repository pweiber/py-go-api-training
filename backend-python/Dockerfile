# Multi-stage build for production-ready Python FastAPI application
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 1. Create the non-root user FIRST
RUN useradd -m -u 1000 appuser

# 2. Copy Python dependencies to the appuser's home directory and give them ownership
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# 3. Copy application code and give ownership to appuser
COPY --chown=appuser:appuser . /app

# Update the PATH to point to the new location
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to the non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]