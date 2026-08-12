# Flask Repository Starter

A reusable backend starter for building serious Flask applications with a clean **Repository → Service → Route** structure, PostgreSQL persistence, JWT authentication, and role/permission-based authorization.

The project is intentionally small and domain-agnostic. It provides the infrastructure that many real applications need before business-specific features are added.

## Why this project exists

Starting a new backend often means rebuilding the same foundation: application setup, database sessions, authentication, authorization, validation, migrations, and error handling.

This repository keeps that foundation in one focused project so it can be:

- used as a starting point for future Flask applications;
- extended without carrying unrelated business-domain code;
- used to practice testing, tooling, CI/CD, deployment, and other engineering concerns in isolation;
- used as a reference implementation for layered Python backend architecture.

## Features

- Flask application factory
- PostgreSQL database
- SQLAlchemy 2.x ORM
- Repository pattern for persistence
- Service layer for application logic
- Marshmallow request/response validation
- JWT authentication with Flask-JWT-Extended
- User registration and login
- Authenticated current-user endpoint
- Role-based access model
- Fine-grained permissions
- User, role, and permission management
- Role-permission assignment
- Centralized application error handling
- Alembic database migrations
- Idempotent seed script
- Pipenv dependency management
- Ruff and Black development tooling

## Tech Stack

| Area                       | Technology         |
| -------------------------- | ------------------ |
| Framework                  | Flask              |
| ORM                        | SQLAlchemy 2.x     |
| Database                   | PostgreSQL         |
| Migrations                 | Alembic            |
| Authentication             | Flask-JWT-Extended |
| Validation / Serialization | Marshmallow        |
| PostgreSQL Driver          | psycopg            |
| Environment Configuration  | python-dotenv      |
| Dependency Management      | Pipenv             |
| Formatting                 | Black              |
| Linting                    | Ruff               |

## Architecture

The application separates responsibilities into four main layers:

**Routes**
Handle HTTP concerns such as request parsing, authentication decorators, response payloads, and status codes.

**Services**
Contain application rules and coordinate operations between repositories and related domain objects.

**Repositories**
Encapsulate database queries and persistence operations.

**Models**
Define SQLAlchemy entities and relationships.

This keeps HTTP, application logic, and persistence concerns from becoming tightly coupled and makes the project easier to extend and test.

## Core Domain

The starter includes three generic authorization entities:

- **User** — an authenticated application account.
- **Role** — groups permissions and can be assigned to users.
- **Permission** — represents an allowed application action.

The seed currently creates two baseline roles:

- **Admin** — receives all seeded management permissions.
- **User** — the default standard-user role and intentionally receives no administrative permissions.

Self-service behavior such as viewing or editing one's own profile can be handled separately through authenticated identity/ownership rules rather than granting broad user-management permissions.

## Project Structure

```text
.
├── app/
│   ├── auth/
│   ├── common/
│   │   └── exceptions/
│   ├── config/
│   ├── permissions/
│   ├── roles/
│   ├── users/
│   ├── associations.py
│   └── __init__.py
├── migrations/
├── scripts/
│   └── seed.py
├── .env.example
├── .gitignore
├── alembic.ini
├── Pipfile
├── Pipfile.lock
├── README.md
└── run.py
```

## Getting Started

### Prerequisites

You will need:

- Python 3.14
- Pipenv
- PostgreSQL

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd flask-repository-starter
```

### 2. Install dependencies

```bash
pipenv install --dev
```

### 3. Create a PostgreSQL database

For local development, create a database such as:

```text
starter_db_dev
```

For example, from `psql`:

```sql
CREATE DATABASE starter_db_dev;
```

### 4. Configure environment variables

Copy the example file:

```bash
cp .env.example .env
```

Then provide your local values:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/starter_db_dev
JWT_SECRET_KEY=YOUR_SECURE_RANDOM_SECRET

ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=CHANGE_ME
ADMIN_FIRST_NAME=System
ADMIN_LAST_NAME=Admin
```

Never commit the real `.env` file.

### 5. Apply database migrations

```bash
pipenv run alembic upgrade head
```

### 6. Seed authorization data

```bash
pipenv run python -m scripts.seed
```

The seed creates the baseline permissions, `Admin` and `User` roles, assigns management permissions to `Admin`, and creates the initial administrator account.

### 7. Start the application

```bash
pipenv run python run.py
```

The development server will normally be available at:

```text
http://127.0.0.1:5000
```

## API Overview

### Authentication

| Method | Endpoint             | Purpose                                  |
| ------ | -------------------- | ---------------------------------------- |
| `POST` | `/api/auth/register` | Register a standard user                 |
| `POST` | `/api/auth/login`    | Authenticate and receive an access token |
| `GET`  | `/api/auth/me`       | Return the authenticated user            |

### Users

| Method   | Endpoint                    | Permission         |
| -------- | --------------------------- | ------------------ |
| `GET`    | `/api/users/`               | `user.read`        |
| `GET`    | `/api/users/<user_id>`      | `user.read`        |
| `POST`   | `/api/users/`               | `user.create`      |
| `PATCH`  | `/api/users/<user_id>`      | `user.update`      |
| `DELETE` | `/api/users/<user_id>`      | `user.delete`      |
| `PATCH`  | `/api/users/<user_id>/role` | `user.change_role` |

### Roles

| Method   | Endpoint                                           | Permission               |
| -------- | -------------------------------------------------- | ------------------------ |
| `GET`    | `/api/roles/`                                      | `role.read`              |
| `GET`    | `/api/roles/<role_id>`                             | `role.read`              |
| `POST`   | `/api/roles/`                                      | `role.create`            |
| `PATCH`  | `/api/roles/<role_id>`                             | `role.update`            |
| `DELETE` | `/api/roles/<role_id>`                             | `role.delete`            |
| `POST`   | `/api/roles/<role_id>/permissions`                 | `role.assign_permission` |
| `DELETE` | `/api/roles/<role_id>/permissions/<permission_id>` | `role.assign_permission` |

### Permissions

| Method   | Endpoint                           | Permission          |
| -------- | ---------------------------------- | ------------------- |
| `GET`    | `/api/permissions/`                | `permission.read`   |
| `GET`    | `/api/permissions/<permission_id>` | `permission.read`   |
| `POST`   | `/api/permissions/`                | `permission.create` |
| `PATCH`  | `/api/permissions/<permission_id>` | `permission.update` |
| `DELETE` | `/api/permissions/<permission_id>` | `permission.delete` |

## Authentication and Authorization

Authentication and authorization are intentionally separate concerns.

A valid JWT proves that a request belongs to an authenticated user.

Administrative routes then use permission checks to determine whether that user's role is allowed to perform the requested action.

This makes authorization more flexible than hardcoding checks such as `role == "Admin"` throughout the application. New roles can be introduced later by assigning the appropriate permissions instead of rewriting route logic.

## Database Migrations

After changing SQLAlchemy models:

```bash
pipenv run alembic revision --autogenerate -m "describe the change"
```

Always inspect the generated migration before applying it.

Then run:

```bash
pipenv run alembic upgrade head
```

## Development Tools

Run Ruff:

```bash
pipenv run ruff check .
```

Run Black:

```bash
pipenv run black .
```

## Design Goals

This starter deliberately favors:

- clear responsibility boundaries over large framework abstractions;
- explicit SQLAlchemy session handling;
- reusable authentication and authorization infrastructure;
- small, understandable layers;
- migrations instead of automatic table creation;
- configuration through environment variables;
- domain independence.

It is **not** intended to contain every feature a Flask application could need. Business-domain models, background jobs, caching, external integrations, and other infrastructure should be added only when a real project requires them.

## Possible Next Improvements

Useful future extensions include:

- unit and integration tests;
- test database configuration;
- coverage reporting;
- pre-commit hooks;
- Docker development setup;
- GitHub Actions CI;
- automated lint/test checks;
- deployment configuration.

## Using This Starter

For a new application:

1. create a project from this repository;
2. configure its database and secrets;
3. keep the authentication/authorization foundation;
4. add the new application's domain models and repositories;
5. build business features vertically through repository, service, and route layers;
6. add project-specific permissions only when they represent real authorization requirements.

The goal is to provide a strong starting point without dictating the business domain that comes next.
:::
