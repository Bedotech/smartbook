# Backend Dockerfile for Smartbook FastAPI application
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml uv.lock* README.md ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

# Install Python dependencies
RUN uv sync

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8000/api/health || exit 1

# Run database migrations and start the application
CMD ["sh", "-c", "/root/.local/bin/uv run alembic upgrade head && /root/.local/bin/uv run uvicorn smartbook.main:app --host 0.0.0.0 --port 8000"]
