FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app
ENV PYTHONPATH=/usr/src/app/src:$PYTHONPATH

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip && pip install poetry
RUN poetry config virtualenvs.create false

COPY ./pyproject.toml ./poetry.lock ./
COPY ./src ./src

RUN poetry install --no-root --with test

