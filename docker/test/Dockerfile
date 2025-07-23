FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app
ENV PYTHONPATH=/usr/src/app

RUN apt update && apt install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    postgresql-client \
    dos2unix \
    && apt clean

RUN pip install --upgrade pip && pip install poetry
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only main,dev

COPY src ./src
COPY alembic.ini ./

COPY commands/entrypoint.sh /commands/entrypoint.sh
RUN chmod +x /commands/entrypoint.sh

ENTRYPOINT ["/commands/entrypoint.sh"]
