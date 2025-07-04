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
    dos2unix \
    && apt clean

# install Poetry
RUN python -m pip install --upgrade pip && pip install poetry
RUN poetry config virtualenvs.create false

# Copy poetry project files
COPY ./poetry.lock ./
COPY ./pyproject.toml ./

# Install dependencies
RUN poetry install --no-root --only main

# Copy the application code
COPY ./src ./src
COPY ./alembic.ini ./

COPY ./commands/entrypoint.sh /commands/entrypoint.sh
RUN chmod +x /commands/entrypoint.sh
ENTRYPOINT ["/commands/entrypoint.sh"]
