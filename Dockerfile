FROM python:3.12-slim

WORKDIR /code

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git config --global --add safe.directory /code

RUN pip install --upgrade pip && \
    pip install uv

COPY pyproject.toml uv.lock* ./README.md ./

RUN uv sync --frozen --no-dev

COPY ./app/ /code/app/

WORKDIR /code/app

ENV PYTHONPATH=/code