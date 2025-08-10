FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app
ENV PYTHONPATH=/usr/src/app/src:$PYTHONPATH

RUN apt update && apt install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    postgresql-client \
    && apt clean

RUN python -m pip install --upgrade pip && pip install poetry
RUN poetry config virtualenvs.create false

COPY ./pyproject.toml ./poetry.lock ./
COPY ./src ./src

RUN poetry install --no-root --with dev,test
