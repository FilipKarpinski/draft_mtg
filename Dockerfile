# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Configure git for pre-commit
RUN git config --global --add safe.directory /code

# Install uv
RUN pip install --upgrade pip && \
    pip install uv

# Copy dependency files first (for better caching)
COPY pyproject.toml uv.lock* ./README.md ./

# Install dependencies without dev dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY ./app /code/app

# Set Python path
ENV PYTHONPATH=/code