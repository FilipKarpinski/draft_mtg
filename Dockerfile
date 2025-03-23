# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /code

# git is required to run pre-commit
RUN apt-get update && apt-get install -y \
    git

# allows pre-commit to run
RUN git config --global --add safe.directory /code

RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false --local

COPY ./pyproject.toml ./poetry.lock* /code/

COPY ./app /code/app

# Install dependencies
RUN poetry install --no-root