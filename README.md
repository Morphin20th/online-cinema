# Online Cinema API

A modular, role-based REST API for managing user accounts, authentication, content moderation, and administration tasks using FastAPI, SQLAlchemy, JWT, Celery, and more.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Tech Stack](#tech-stack)
4. [Getting Started](#getting-started)
5. [Project Structure](#project-structure)
6. [API Documentation](#api-documentation)
7. [Database Models](#database-models)

---

## Overview

A backend service designed for a movie catalog and management platform with user and admin interfaces. This project supports secure user authentication, registration workflows, password management, role-based permissions, and scalable background task handling.

---

## Features
- 🔐 JWT-based login/logout with access/refresh token flow 
- ✅ Email-based user activation
- 🔒 Token blacklisting on logout (via Redis)
- ⏱ Auto-clean expired tokens using Celery Beat

---

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy
- **Database:** PostgreSQL
- **Auth:** JWT, Redis blacklist
- **Background Tasks:** Celery + Celery Beat, Redis broker
- **Email Service:** SMTP

---

## Getting Started

Follow these steps to set up and run the project in your local development environment.
1. Clone the Repository

```bash
git clone https://github.com/Morphin20th/online-cinema.git
cd online-cinema
```

2. Set Up Environment Variables

```bash
cp .env.sample .env
```

3. Create and Activate Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

4. Install Dependencies

```bash
pip install poetry
poetry install
```

5. Start Required Services

```bash
sudo systemctl start postgresql
sudo systemctl start redis
```

6. Run Mailhog 

Use Docker Compose to start Mailhog:

```bash
docker compose up -d mailhog
```
> Mailhog web UI: http://localhost:8026

7. Apply Migrations

```bash
alembic upgrade head
```

8. Run the Server

```bash
uvicorn main:app --reload --port 8001
```

> API will be running at: http://localhost:8001

---

## Project Structure

--- 
```
.
├── alembic.ini
├── docker-compose.yml
├── poetry.lock
├── pyproject.toml
├── README.md
└── src
    ├── config
    │   ├── config.py
    │   ├── dependencies.py
    │   └── __init__.py
    ├── database
    │   ├── __init__.py
    │   ├── migrations
    │   │   ├── env.py
    │   │   ├── script.py.mako
    │   │   └── versions
    │   │       ├── a1b67ffb1410_update_updated_at_field_at_usermodel.py
    │   │       └── b54930467e86_initial.py
    │   ├── models
    │   │   ├── accounts.py
    │   │   ├── base.py
    │   │   └── __init__.py
    │   ├── session.py
    │   ├── startup_data.py
    │   └── utils.py
    ├── __init__.py
    ├── main.py
    ├── routes
    │   ├── accounts.py
    │   ├── administration.py
    │   ├── __init__.py
    │   └── profiles.py
    ├── schemas
    │   ├── accounts.py
    │   ├── administration.py
    │   ├── __init__.py
    │   └── profiles.py
    ├── security
    │   ├── dependencies.py
    │   ├── __init__.py
    │   ├── password.py
    │   └── token_manager.py
    ├── services
    │   ├── email_service.py
    │   ├── __init__.py
    │   └── templates
    │       └── emails
    │           ├── activation_confirmation.html
    │           ├── activation.html
    │           ├── base.html
    │           ├── password_reset_completion.html
    │           └── password_reset_request.html
    ├── storage
    │   └── media
    │       └── avatars
    ├── tasks_manager
    │   ├── celery_app.py
    │   ├── __init__.py
    │   ├── tasks
    │   │   ├── cleanup.py
    │   │   └── __init__.py
    │   └── temp.py
    └── validation
        ├── __init__.py
        ├── profile_validators.py
        └── security_validators.py

```
---

### **Root Directory**
- **`README.MD`**: Main project documentation.
- **`poetry.lock`** & **`pyproject.toml`**: Poetry-based dependency management.
- **`docker-compose.yml`**: Run Mailhog

### **Source Directory (`src`)**


#### **Configuration (`config`)**
- **`dependencies.py`**: Defines FastAPI dependencies for dependency injection.
- **`config.py`**: Manages project settings, including database configurations and external service settings.

#### **Database (`database`)**
- **`session.py`**: Initializes the SQLAlchemy session and engine.
- **`utils.py`**: Contains utility functions for database operations.
- **`models/`**: SQLAlchemy ORM models for Users, Groups, Tokens, etc.
- **`migrations/`**: Alembic migration environment and revision files.
  - **`env.py`**: Alembic environment configuration.
  - **`versions/`**: Individual migration scripts.

#### **Routes (`routes`)**
- **`accounts.py`**: Endpoints for registration, login, password management, activation.
- **`profiles.py`**: User profile-related routes.
- **`administration.py`**: Admin/moderator-only endpoints (user/group management).

#### **Schemas (`schemas`)**
- **`accounts.py`**: Pydantic schemas for auth, login, activation, password reset, etc.
- **`profiles.py`**: Schemas for profile details and updates.
- **`administration.py`**: Schemas related to admin-level operations.

#### **Security (`security`)**
- **`token_manager.py`**: Handles JWT token creation, decoding, validation.
- **`password.py`**: Password hashing and verification logic.
- **`dependencies.py`**: Security-related dependencies (e.g. current user, permissions).

#### **Services (`services`)**
- **`email_service.py`**: Sends email messages (activation, password reset, etc.).
- **`templates/emails/`**: HTML templates for various email types.


#### **Storage (`storage`)**
- **`media/avatars/`**: Directory for storing uploaded user avatar images.


#### **Tasks Manager (`tasks_manager`)**
- **`celery_app.py`**: Celery application initialization.
- **`tasks/`**: Celery task modules.
  - **`cleanup.py`**: Periodically deletes expired tokens (activation/password reset).

#### **Validation (`validation`)**
- **`profile_validators.py`**: Custom Pydantic or manual validators for profile data.
- **`security_validators.py`**: Password complexity rules and other auth-related checks.

## API Documentation

> localhost:8001/docs/

---

