FROM python:3.11-slim

# Setting environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /usr/src/app
ENV PYTHONPATH=/usr/src/app

# Installing dependecies
RUN apt update && apt install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    postgresql-client \
    && apt clean

# install Poetry
RUN python -m pip install --upgrade pip && pip install poetry
RUN poetry config virtualenvs.create false

# Copy poetry project files
COPY ./pyproject.toml ./poetry.lock ./

# Install dependencies
RUN poetry install --no-root --only main

# Copy the application code
COPY ./src ./src
COPY ./alembic.ini ./
