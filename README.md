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
- **Pytest**: Tests

---
Here's a refined **Getting Started** section that strongly recommends Docker while keeping Poetry instructions for developers who need them:

---

## Getting Started

For the best experience, I **recommend using Docker** as it handles all dependencies automatically. Local setup with Poetry is provided for development purposes.

### Docker Setup
```bash
git clone https://github.com/Morphin20th/online-cinema.git
cd online-cinema

# 1. Configure environment
cp config_envs/.env.sample .env  # Edit with your values

# 2. Start all services (FastAPI, PostgreSQL, Redis, Celery, Mailhog, Stripe CLI)
docker compose -f docker-compose.yml up --build
```

Access:
- API: `http://localhost:8001`
- Mailhog: `http://localhost:8025`


### Run with Docker

```bash
docker compose up --build
```

> Mailhog web UI: http://localhost:8025

> API will be running at: http://localhost:8001

---

## Project Structure

--- 
```
.
├── alembic.ini
├── config_envs
├── docker
│   └── test
│       └── Dockerfile
├── docker-compose-tests.yml
├── docker-compose.yml
├── Dockerfile
├── poetry.lock
├── pyproject.toml
├── pytest.ini
├── README.md
└── src
    ├── __init__.py
    ├── main.py
    ├── config
    │   ├── __init__.py
    │   ├── api.py
    │   ├── celery.py
    │   ├── config.py
    │   ├── database.py
    │   ├── email.py
    │   ├── payment.py
    │   ├── security.py
    │   └── settings.py
    ├── database
    │   ├── __init__.py
    │   ├── migrations
    │   │   ├── env.py
    │   │   ├── script.py.mako
    │   │   └── versions
    │   │       └── 47d6f267234e_initial_tables.py
    │   ├── models
    │   │   ├── __init__.py
    │   │   ├── accounts.py
    │   │   ├── base.py
    │   │   ├── carts.py
    │   │   ├── enums.py
    │   │   ├── movies.py
    │   │   ├── orders.py
    │   │   ├── payments.py
    │   │   └── purchases.py
    │   └── session_postgres.py
    ├── dependencies
    │   ├── __init__.py
    │   ├── auth.py
    │   ├── config.py
    │   └── group.py 
    ├── routes
    │   ├── __init__.py
    │   ├── accounts.py
    │   ├── administration.py
    │   ├── carts.py
    │   ├── docs.py
    │   ├── movies
    │   │   ├── __init__.py
    │   │   ├── genres.py
    │   │   ├── movies.py
    │   │   ├── movie_utils.py
    │   │   └── stars.py
    │   ├── orders.py
    │   ├── payments.py
    │   └── profiles.py
    ├── schemas
    │   ├── __init__.py
    │   ├── accounts.py
    │   ├── administration.py
    │   ├── carts.py
    │   ├── common.py
    │   ├── examples.py
    │   ├── _mixins.py
    │   ├── movies.py
    │   ├── orders.py
    │   ├── payments.py
    │   └── profiles.py
    ├── security
    │   ├── __init__.py
    │   ├── interfaces.py
    │   ├── password.py
    │   └── token_manager.py
    ├── services
    │   ├── __init__.py
    │   ├── email_interface.py
    │   ├── email_service.py
    │   ├── stripe_interface.py
    │   ├── stripe.py
    │   └── templates
    │       └── emails
    │           ├── activation_confirmation.html
    │           ├── activation.html
    │           ├── base.html
    │           ├── password_reset_completion.html
    │           ├── password_reset_request.html
    │           └── payment_success.html
    ├── storage
    │   └── media
    │       └── avatars
    ├── tasks_manager
    │   ├── __init__.py
    │   ├── celery_app.py
    │   └── tasks
    │       ├── __init__.py
    │       └── cleanup.py
    ├── tests
    │   ├── api
    │   │   ├── __init__.py
    │   │   ├── test_accounts.py
    │   │   ├── test_administration.py
    │   │   ├── test_carts.py
    │   │   ├── test_dependencies.py
    │   │   ├── test_docs.py
    │   │   ├── test_genres.py
    │   │   ├── test_movies.py
    │   │   ├── test_orders.py
    │   │   ├── test_pagination.py
    │   │   ├── test_payments.py
    │   │   ├── test_profiles.py
    │   │   └── test_stars.py
    │   ├── conftest.py
    │   ├── examples
    │   │   ├── __init__.py
    │   │   ├── movie_examples.py
    │   │   └── profile_examples.py
    │   ├── __init__.py
    │   ├── services
    │   │   ├── __init__.py
    │   │   ├── test_email_service.py
    │   │   └── test_stripe_service.py
    │   ├── stubs
    │   │   ├── email.py
    │   │   └── __init__.py
    │   ├── tasks
    │   │   ├── __init__.py
    │   │   └── test_cleanup.py
    │   └── utils
    │       ├── factories.py
    │       ├── fixtures
    │       │   ├── carts.py
    │       │   ├── clients.py
    │       │   ├── __init__.py
    │       │   ├── movies.py
    │       │   ├── orders.py
    │       │   └── payments.py
    │       ├── __init__.py
    │       └── utils.py
    ├── utils
    │   ├── __init__.py
    │   ├── openapi.py
    │   ├── pagination.py
    │   └── token_generation.py
    └── validation
        ├── __init__.py
        ├── profile_validators.py
        └── security_validators.py

```
---

### **Root Directory**
- `README.MD`: Main project documentation.
- `poetry.lock` & `pyproject.toml`: Poetry-based dependency management.
- `docker-compose.yml`: Defines and manages multi-container Docker applications (FastAPI app, PostgreSQL, Redis, Celery, Mailhog).
- `docker-compose-tests.yml`: Configuration for test environment containers.
- `Dockerfile`: Builds the FastAPI application image with all dependencies and startup logic.
- `alembic.ini`: Configuration file for Alembic database migrations.
- `pytest.ini`: Configuration file for pytest test runner.

### **Config environments (`config_env/`)**
- `.env.prod.sample` - Sample of variables to use in production environment 
- `.env.sample` - Sample of variables to use in development environment  
- `.env.test.sample` - Sample of variables to use in test environment

### **Dockerfiles (`docker/`)**
- `test/`
  - `Dockerfile` - Dockerfile for test environment

### **Source Directory (`src/`)**

#### Configuration (`config/`)
- `api.py` - Configurations for URLs 
- `config.py` - Base configuration loader and environment setup
- `celery.py` - Celery task queue config with Redis broker settings  
- `database.py` - Database connection strings and ORM configurations
- `email.py` - SMTP server settings and email delivery parameters
- `payment.py` - Stripe API keys and payment gateway settings
- `security.py` - JWT authentication and password hashing configs  
- `settings.py` - Core application settings

Each file handles specific service configurations with environment variables.

#### Database (`database/`)
- `session_postgres.py`: Initializes the SQLAlchemy PostgreSQL session and engine.
- `models/`: SQLAlchemy ORM models for Users, Movies, Carts, etc.
- `migrations/`: Alembic migration environment and revision files.
  - `env.py`: Alembic environment configuration.
  - `versions/`: Individual migration scripts.

#### Dependencies (`dependencies/`)
- `auth.py`: Authentication and User dependencies.
- `config.py`: Project Configuration dependencies.
- `group.py`: User groups dependencies.

#### Routes (`routes/`)
- `accounts.py`: Endpoints for registration, login, password management, activation.
- `profiles.py`: User profile-related routes.
- `administration.py`: Admin-only endpoints (user/group management).
- `carts.py`: Cart-related endpoints.
- `orders.py`: Order-related endpoints.
- `payments.py`: Payment-related endpoints.
- `docs.py`: Configuration for docs access.
- `movies/`: Movie depended endpoints.
  -  `genres.py`: Genre endpoints.
  -  `movies.py`: Movie endpoints.
  -  `stars.py`: Star endpoints.

#### Schemas (`schemas/`)
- `_mixins.py`: Mixins for all schemas to use.
- `accounts.py`: Pydantic schemas for auth, login, activation, password reset, etc.
- `profiles.py`: Schemas for profile details and updates.
- `administration.py`: Schemas related to admin-level operations.
- `common.py`: Common schemas used by every route type.
- `movies.py`: Movie, genre, star and director schemas.
- `carts.py`: Carts schemas.
- `orders.py`: Order schemas.
- `payments.py`: Payment schemas.
- `examples.py`: Examples of HTTPExceptions for OpenAPI.

#### Security (`security/`)
- `interfaces.py`: JWTAuthManager interface.
- `token_manager.py`: Handles JWT token creation, decoding, validation.
- `password.py`: Password hashing and verification logic.

#### Services (`services/`)
- `email_interface.py`: EmailSender interface.
- `email_service.py`: Sends email messages (activation, password reset, etc.).
- `stripe_interface.py`: Stripe interface
- `stripe.py`: Manages Stripe payment operations
- `templates/emails/`: HTML templates for various email types.

#### Storage (`storage/`)
- `media/avatars/`: Directory for storing uploaded user avatar images.

#### Tasks Manager (`tasks_manager/`)
- `celery_app.py`: Celery application initialization.
- `tasks/`: Celery task modules.
  - `cleanup.py`: Periodically deletes expired tokens (activation/password reset).

#### Validation (`validation/`)
- `profile_validators.py`: Custom Pydantic or manual validators for profile data.
- `security_validators.py`: Password complexity rules and other auth-related checks.

#### Utils (`utils/`)
- `pagination.py`: Pagination link building.
- `token_generation.py`: Secure token generation.

#### Tests (`tests/`)
- `conftest.py` - Shared pytest fixtures and configuration
- `api/` - API endpoint tests (routes, validation, auth)
- `examples/` - Sample data for test cases
- `services/` - Service tests (email, payments)
- `stubs/` - Stubs for services
- `tasks/` - Celery task tests
- `utils/` - Utilities for tests (helpers, factories)
  - `utils/fixtures/` - Complex test fixtures (DB models etc.)

## API Documentation

> localhost:8001/docs/

Admin privileges required.

---

## Database Models

The project defines the following entities and relationships using SQLAlchemy. Each entity represents a table in the database and maps to a specific domain concept in the Online Cinema API.

## Accounts Models

These models handle user authentication, authorization, and related functionality.

### 1. UserGroupModel

Represents user groups in the application (e.g., USER, MODERATOR, ADMIN).

- **Table Name**: `user_groups`
- **Fields**:
    - `id` (Primary Key): Unique identifier for each user group.
    - `name`: Enum value representing the group (`UserGroupEnum` with values: ADMIN, USER, MODERATOR).

- **Relationships**:
    - `users`: One-to-many relationship with `UserModel`.

- **Constraints**:
    - Unique constraint on `name`.

### 2. UserModel

Represents application users with authentication details.

- **Table Name**: `users`
- **Fields**:
    - `id` (Primary Key): Unique identifier for each user.
    - `email`: String value representing user's email (max 255 chars, unique, indexed).
    - `_hashed_password`: Securely stored password hash (max 255 chars).
    - `is_active`: Boolean indicating whether the user account is active (defaults to False).
    - `created_at`: Timestamp when the user was created (server default to current time).
    - `updated_at`: Timestamp when the user was last updated (auto-updates on modification).
    - `group_id`: Foreign key linking to the `user_groups` table (on delete CASCADE).

- **Relationships**:
    - `group`: Many-to-one relationship with `UserGroupModel`.
    - `profile`: One-to-one relationship with `UserProfileModel`.
    - `activation_token`: One-to-one relationship with `ActivationTokenModel`.
    - `password_reset_token`: One-to-one relationship with `PasswordResetTokenModel`.
    - `refresh_tokens`: One-to-many relationship with `RefreshTokenModel`.
    - `cart`: One-to-one relationship with `CartModel`.
    - `purchases`: One-to-many relationship with `PurchaseModel`.
    - `orders`: One-to-many relationship with `OrderModel`.
    - `payments`: One-to-many relationship with `PaymentModel`.

- **Methods**:
    - `password`: Property (write-only) for setting passwords.
    - `verify_password`: Verifies if provided password matches the hash.
    - `create`: Class method for creating new users.

### 3. UserProfileModel

Stores additional user profile information.

- **Table Name**: `user_profiles`
- **Fields**:
    - `id` (Primary Key): Unique identifier.
    - `first_name`: Optional string (max 100 chars) for user's first name.
    - `last_name`: Optional string (max 100 chars) for user's last name.
    - `avatar`: Optional string (max 255 chars) for avatar URL/path.
    - `gender`: Optional enum (`GenderEnum` with values: MAN, WOMAN).
    - `date_of_birth`: Optional date field.
    - `info`: Optional text field for additional information.
    - `user_id`: Foreign key to `users` table (on delete CASCADE, unique).

- **Relationships**:
    - `user`: One-to-one relationship with `UserModel`.

### 4. TokenBaseModel (Abstract)

Base model for token-based operations (abstract, not directly instantiated).

- **Fields**:
    - `id` (Primary Key): Unique identifier.
    - `token`: String token value (64 chars by default, unique).
    - `expires_at`: DateTime when token expires (defaults to 1 day from creation).
    - `user_id`: Foreign key to `users` table (on delete CASCADE).

### 5. ActivationTokenModel

Handles account activation tokens (inherits from TokenBaseModel).

- **Table Name**: `activation_tokens`
- **Relationships**:
    - `user`: One-to-one relationship with `UserModel`.

- **Constraints**:
    - Unique constraint on `user_id`.

- **Methods**:
    - `create`: Class method for creating activation tokens with custom expiration.

### 6. PasswordResetTokenModel

Handles password reset tokens (inherits from TokenBaseModel).

- **Table Name**: `password_reset_tokens`
- **Relationships**:
    - `user`: One-to-one relationship with `UserModel`.

- **Constraints**:
    - Unique constraint on `user_id`.

### 7. RefreshTokenModel

Manages refresh tokens for authentication (inherits from TokenBaseModel).

- **Table Name**: `refresh_tokens`
- **Fields**:
    - `token`: Extended string token value (512 chars, unique).

- **Relationships**:
    - `user`: One-to-one relationship with `UserModel`.

- **Constraints**:
    - Unique constraint on `user_id`.

- **Methods**:
    - `create`: Class method for creating refresh tokens with custom expiration.

## Movie Models

These models handle movie data, including metadata, cast/crew information, and classifications.

### 1. Association Tables

Three association tables handle many-to-many relationships between movies and their related entities:

#### MoviesGenresTable
- **Table Name**: `movies_genres`
- **Fields**:
  - `movie_id`: Foreign key to `movies.id` (on delete CASCADE, primary key)
  - `genre_id`: Foreign key to `genres.id` (on delete CASCADE, primary key)

#### MoviesStarsTable
- **Table Name**: `movies_stars`
- **Fields**:
  - `movie_id`: Foreign key to `movies.id` (on delete CASCADE, primary key)
  - `star_id`: Foreign key to `stars.id` (on delete CASCADE, primary key)

#### MoviesDirectorsTable
- **Table Name**: `movies_directors`
- **Fields**:
  - `movie_id`: Foreign key to `movies.id` (on delete CASCADE, primary key)
  - `director_id`: Foreign key to `directors.id` (on delete CASCADE, primary key)

### 2. GenreModel

Represents movie genres/categories.

- **Table Name**: `genres`
- **Fields**:
  - `id` (Primary Key): Unique identifier
  - `name`: Genre name (max 100 chars, unique)

- **Relationships**:
  - `movies`: Many-to-many relationship with `MovieModel` through `MoviesGenresTable`

### 3. StarModel

Represents actors/performers in movies.

- **Table Name**: `stars`
- **Fields**:
  - `id` (Primary Key): Unique identifier
  - `name`: Star's name (max 100 chars, unique)

- **Relationships**:
  - `movies`: Many-to-many relationship with `MovieModel` through `MoviesStarsTable`

### 4. DirectorModel

Represents movie directors.

- **Table Name**: `directors`
- **Fields**:
  - `id` (Primary Key): Unique identifier
  - `name`: Director's name (max 100 chars, unique)

- **Relationships**:
  - `movies`: Many-to-many relationship with `MovieModel` through `MoviesDirectorsTable`

### 5. CertificationModel

Represents age/content ratings for movies (e.g., PG-13, R).

- **Table Name**: `certifications`
- **Fields**:
  - `id` (Primary Key): Unique identifier
  - `name`: Certification name (max 100 chars, unique)

- **Relationships**:
  - `movies`: One-to-many relationship with `MovieModel`

### 6. MovieModel

Main model representing movies in the system.

- **Table Name**: `movies`
- **Fields**:
  - `id` (Primary Key): Unique identifier
  - `uuid`: Universally unique identifier (UUID format)
  - `name`: Movie title (max 250 chars, unique)
  - `year`: Release year
  - `time`: Runtime in minutes
  - `imdb`: IMDB rating (float)
  - `votes`: Number of IMDB votes
  - `meta_score`: Optional Metacritic score
  - `gross`: Optional box office gross earnings
  - `description`: Full movie description (text)
  - `price`: Purchase price (DECIMAL(10,2))
  - `certification_id`: Foreign key to `certifications` table

- **Relationships**:
  - `certification`: Many-to-one relationship with `CertificationModel`
  - `stars`: Many-to-many relationship with `StarModel` through `MoviesStarsTable`
  - `genres`: Many-to-many relationship with `GenreModel` through `MoviesGenresTable`
  - `directors`: Many-to-many relationship with `DirectorModel` through `MoviesDirectorsTable`
  - `cart_items`: One-to-many relationship with `CartItemModel`
  - `purchases`: One-to-many relationship with `PurchaseModel`
  - `order_items`: One-to-many relationship with `OrderItemModel`

- **Constraints**:
  - Unique constraint on combination of `name`, `year`, and `time`

## Cart Models

These models handle shopping cart functionality, allowing users to collect movies before purchase.

### 1. CartModel

Represents a user's shopping cart.

- **Table Name**: `carts`
- **Fields**:
  - `id` (Primary Key): Unique identifier
  - `user_id`: Foreign key to `users.id` (on delete CASCADE, unique constraint)

- **Relationships**:
  - `user`: One-to-one relationship with `UserModel` (each user has exactly one cart)
  - `cart_items`: One-to-many relationship with `CartItemModel` (items in the cart)

### 2. CartItemModel

Represents individual items in a shopping cart.

- **Table Name**: `cart_items`
- **Fields**:
  - `id` (Primary Key): Unique identifier
  - `added_at`: Timestamp when item was added to cart (server default to current time)
  - `cart_id`: Foreign key to `carts.id` (on delete CASCADE)
  - `movie_id`: Foreign key to `movies.id` (on delete CASCADE)

- **Relationships**:
  - `cart`: Many-to-one relationship with `CartModel`
  - `movie`: Many-to-one relationship with `MovieModel`

- **Constraints**:
  - Unique constraint on combination of `cart_id` and `movie_id` (prevents duplicate movie entries in the same cart)

Here's the documentation for the Order Models in the requested format:

## Order Models

These models handle order processing and management for movie purchases.

### 1. OrderStatusEnum

Defines possible order statuses:

- `PENDING`: Order created but not yet paid (default status)
- `PAID`: Order successfully paid
- `CANCELLED`: Order was cancelled

### 2. OrderModel

Represents a customer order containing one or more movies.

- **Table Name**: `orders`
- **Fields**:
  - `id` (Primary Key): Unique identifier
  - `user_id`: Foreign key to `users.id` (on delete CASCADE)
  - `created_at`: Timestamp when order was created (server default to current time)
  - `status`: Order status (OrderStatusEnum, defaults to PENDING)
  - `total_amount`: Calculated total order amount (DECIMAL(10,2), nullable)

- **Relationships**:
  - `user`: Many-to-one relationship with `UserModel` (order owner)
  - `order_items`: One-to-many relationship with `OrderItemModel`
  - `payments`: One-to-many relationship with `PaymentModel`

- **Properties**:
  - `total`: Computes sum of all movie prices in the order

### 3. OrderItemModel

Represents individual movie items within an order.

- **Table Name**: `order_items`
- **Fields**:
  - `id` (Primary Key): Unique identifier
  - `order_id`: Foreign key to `orders.id` (on delete CASCADE)
  - `movie_id`: Foreign key to `movies.id` (on delete CASCADE)

- **Relationships**:
  - `order`: Many-to-one relationship with `OrderModel`
  - `movie`: Many-to-one relationship with `MovieModel`
  - `payment_items`: One-to-many relationship with `PaymentItemModel`

## Purchase Models

This model handles movie purchase records, tracking which users have purchased which movies.

### 1. PurchaseModel

Represents a movie purchase by a user.

- **Table Name**: `purchases`
- **Fields**:
  - `id` (Primary Key): Unique identifier
  - `purchased_at`: Timestamp when purchase was made (server default to current time)
  - `user_id`: Foreign key to `users.id` (on delete CASCADE)
  - `movie_id`: Foreign key to `movies.id` (on delete CASCADE)

- **Relationships**:
  - `user`: Many-to-one relationship with `UserModel` (links to purchasing user)
  - `movie`: Many-to-one relationship with `MovieModel` (links to purchased movie)

- **Constraints**:
  - Unique constraint on combination of `user_id` and `movie_id` (prevents duplicate purchases of same movie by same user)

## Payment Models

These models handle payment processing and transaction records for movie purchases.

### 1. PaymentStatusEnum

Defines possible payment statuses:

- `SUCCESSFUL`: Payment completed successfully
- `CANCELLED`: Payment was cancelled
- `REFUNDED`: Payment was refunded

### 2. PaymentModel

Represents a payment transaction.

- **Table Name**: `payments`
- **Fields**:
  - `id` (Primary Key): Unique identifier
  - `created_at`: Timestamp when payment was created (server default to current time)
  - `amount`: Total payment amount (DECIMAL(10,2))
  - `status`: Payment status (PaymentStatusEnum, defaults to SUCCESSFUL)
  - `external_payment_id`: Optional reference to external payment processor ID (max 255 chars)
  - `user_id`: Foreign key to `users.id` (on delete CASCADE)
  - `order_id`: Foreign key to `orders.id` (on delete CASCADE)

- **Relationships**:
  - `user`: Many-to-one relationship with `UserModel` (payer)
  - `order`: Many-to-one relationship with `OrderModel`
  - `payment_items`: One-to-many relationship with `PaymentItemModel`

### 3. PaymentItemModel

Represents individual items within a payment (line items).

- **Table Name**: `payment_items`
- **Fields**:
  - `id` (Primary Key): Unique identifier
  - `price_at_payment`: Snapshot of item price at time of payment (DECIMAL(10,2))
  - `payment_id`: Foreign key to `payments.id` (on delete CASCADE)
  - `order_item_id`: Foreign key to `order_items.id` (on delete CASCADE)

- **Relationships**:
  - `payment`: Many-to-one relationship with `PaymentModel`
  - `order_item`: Many-to-one relationship with `OrderItemModel`
