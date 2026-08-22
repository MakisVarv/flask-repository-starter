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
- Current-user profile viewing and editing
- Role-based access model
- Fine-grained permissions
- User, role, and permission management
- User pagination, search, and filtering
- Role-permission assignment
- Centralized application error handling
- Alembic database migrations
- Idempotent seed script
- Separate PostgreSQL test database
- Pytest integration tests
- Coverage reporting with pytest-cov
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
| Testing                    | Pytest             |
| Coverage                   | pytest-cov         |
| PostgreSQL Driver          | psycopg            |
| Environment Configuration  | python-dotenv      |
| Dependency Management      | Pipenv             |
| Formatting                 | Black              |
| Linting                    | Ruff               |

## Architecture

The application separates responsibilities into four main layers:

**Routes**

Handle HTTP concerns such as request parsing, authentication and authorization decorators, response payloads, and status codes.

**Services**

Contain application rules, coordinate repositories, enforce application-level behavior, and own transaction boundaries.

**Repositories**

Encapsulate database queries and persistence operations without owning transaction commits.

**Models**

Define SQLAlchemy entities and relationships.

The typical request flow is:

```text
HTTP Request
    ↓
Route
    ↓
Service
    ↓
Repository
    ↓
SQLAlchemy / PostgreSQL
```

This keeps HTTP, application logic, and persistence concerns from becoming tightly coupled and makes the project easier to extend and test.

## Core Domain

The starter includes three generic authorization entities:

- **User** — an authenticated application account.
- **Role** — groups permissions and can be assigned to users.
- **Permission** — represents an allowed application action.

The seed currently creates two baseline roles:

- **Admin** — receives all seeded permissions.
- **User** — the default standard-user role and intentionally receives no administrative permissions.

Permissions are action-oriented, for example:

```text
user.read
user.create
user.update
user.delete
user.change_role

role.read
role.create
role.update
role.delete
role.assign_permission

permission.read
permission.create
permission.update
permission.delete

dashboard.read
```

`dashboard.read` is included as a simple example of a permission that can later represent business-facing functionality when this starter is extended into a real application.

Self-service behavior such as viewing or editing one's own profile is handled separately through authenticated identity and ownership rules rather than by granting broad administrative user-management permissions.

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
├── tests/
├── .env.example
├── .gitignore
├── alembic.ini
├── Pipfile
├── Pipfile.lock
├── pytest.ini
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

### 3. Create PostgreSQL databases

Create a development database and a separate test database.

For example:

```text
starter_db_dev
starter_db_test
```

From `psql`:

```sql
CREATE DATABASE starter_db_dev;
CREATE DATABASE starter_db_test;
```

Keeping tests on a separate database prevents test execution from affecting development data.

### 4. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Then provide your local values:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/starter_db_dev
TEST_DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/starter_db_test

JWT_SECRET_KEY=YOUR_SECURE_RANDOM_SECRET

ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=CHANGE_ME
ADMIN_FIRST_NAME=System
ADMIN_LAST_NAME=Admin
```

`ADMIN_PASSWORD` must contain at least 8 characters.

Never commit the real `.env` file.

### 5. Apply database migrations

Apply the current schema to the development database:

```bash
pipenv run alembic upgrade head
```

The test database must also have the current Alembic migrations applied before running the test suite.

### 6. Seed authorization data

```bash
pipenv run python -m scripts.seed
```

The seed:

- creates the baseline permissions;
- creates the `Admin` and `User` roles;
- assigns all seeded permissions to `Admin`;
- creates the configured administrator account;
- promotes an existing account with `ADMIN_EMAIL` to the `Admin` role when necessary.

The seed is designed to be idempotent and can be run again without recreating existing roles, permissions, or users.

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

| Method  | Endpoint             | Purpose                                  |
| ------- | -------------------- | ---------------------------------------- |
| `POST`  | `/api/auth/register` | Register a standard user                 |
| `POST`  | `/api/auth/login`    | Authenticate and receive an access token |
| `GET`   | `/api/auth/me`       | Return the authenticated user            |
| `PATCH` | `/api/auth/me`       | Update the authenticated user's profile  |

The current-user update endpoint allows self-service profile fields such as first name, last name, and phone to be changed without granting administrative user-management permissions.

### Users

| Method   | Endpoint                    | Permission         |
| -------- | --------------------------- | ------------------ |
| `GET`    | `/api/users/`               | `user.read`        |
| `GET`    | `/api/users/<user_id>`      | `user.read`        |
| `POST`   | `/api/users/`               | `user.create`      |
| `PATCH`  | `/api/users/<user_id>`      | `user.update`      |
| `DELETE` | `/api/users/<user_id>`      | `user.delete`      |
| `PATCH`  | `/api/users/<user_id>/role` | `user.change_role` |

`GET /api/users/` supports pagination, search, and filtering.

Example:

```text
/api/users/?page=1&page_size=10&search=john&role=Admin&is_active=true
```

Supported query parameters:

- `page` — page number starting at `1`
- `page_size` — number of results per page, from `1` to `100`
- `search` — searches first name, last name, and email
- `role` — filters by role name
- `is_active` — filters active or inactive users

Example response:

```json
{
  "items": [],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 0,
    "total_pages": 0
  }
}
```

Pagination totals are calculated using the same filters applied to the returned user list.

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

A valid JWT proves that a request contains an authenticated identity.

Authentication-only endpoints such as `/api/auth/me` use that identity to resolve the current user.

Administrative routes use permission checks to determine whether the authenticated user's role is allowed to perform the requested action.

Permission-protected routes verify the JWT and then resolve the current user from the database before checking permissions assigned through that user's role.

This means account state continues to be enforced after a token has been issued. For example, if an account becomes inactive, an otherwise valid existing JWT can no longer be used to access authenticated application functionality.

The authorization model avoids hardcoded checks such as:

```python
if user.role.name == "Admin":
    ...
```

Instead, routes depend on named permissions such as:

```text
user.read
role.update
permission.create
```

New roles can therefore be introduced later by assigning the appropriate permissions instead of rewriting route logic.

Administrative user-management routes and self-service routes are deliberately separated.

For example:

```text
GET /api/users/<user_id>
```

requires `user.read`, even when a user attempts to request their own ID.

Self-service access instead belongs to:

```text
GET /api/auth/me
PATCH /api/auth/me
```

This keeps ownership-based behavior separate from administrative authorization.

## Database and Transaction Boundaries

The project uses explicit SQLAlchemy sessions.

Repositories are responsible for persistence operations such as:

- querying;
- adding entities;
- updating entities;
- deleting entities;
- flushing and refreshing when necessary.

Repositories do not own transaction commits.

Services coordinate application operations and own commit and rollback behavior.

This keeps transaction boundaries at the application-service level rather than scattering them across persistence methods.

## Database Migrations

Database schema changes are managed with Alembic.

After changing SQLAlchemy models:

```bash
pipenv run alembic revision --autogenerate -m "describe the change"
```

Always inspect the generated migration before applying it.

Then run:

```bash
pipenv run alembic upgrade head
```

The application does not rely on automatic table creation at startup. Schema evolution should happen through migrations.

## Testing

The project uses Pytest with a dedicated PostgreSQL test database configured through:

```env
TEST_DATABASE_URL
```

The test database should have the current Alembic migrations applied before running the suite.

Run the tests with:

```bash
pipenv run pytest
```

The test infrastructure wraps each test in a database transaction and rolls that transaction back afterward.

This allows tests to exercise real PostgreSQL and SQLAlchemy behavior while keeping tests isolated from one another.

The suite includes representative coverage for:

- registration;
- login;
- invalid credentials;
- JWT authentication;
- permission enforcement;
- current-user retrieval;
- current-user profile updates;
- inactive-account enforcement;
- administrative user access;
- user creation;
- pagination;
- search;
- role filtering;
- active/inactive filtering;
- query validation.

Coverage reporting is configured through `pytest.ini` using `pytest-cov`.

Running the test suite generates terminal coverage information and an HTML coverage report in:

```text
htmlcov/
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

Run the test suite:

```bash
pipenv run pytest
```

These commands provide a simple local quality workflow without requiring additional infrastructure.

## Design Goals

This starter deliberately favors:

- clear responsibility boundaries over large framework abstractions;
- explicit SQLAlchemy session handling;
- service-owned transaction boundaries;
- reusable authentication and authorization infrastructure;
- permission-based authorization instead of hardcoded role checks;
- ownership-aware self-service endpoints;
- small, understandable layers;
- migrations instead of automatic table creation;
- configuration through environment variables;
- isolated integration testing against PostgreSQL;
- domain independence.

It is **not** intended to contain every feature a Flask application could need.

Business-domain models, background jobs, caching, external integrations, queues, scheduled jobs, and other infrastructure should be added only when a real project requires them.

The starter provides a foundation rather than attempting to predict every future application's architecture.

## Possible Next Improvements

Useful future engineering extensions include:

- pre-commit hooks;
- Docker development setup;
- GitHub Actions CI;
- automated lint and test checks;
- deployment configuration.

These should be introduced when they provide practical value rather than simply increasing the number of tools in the project.

## Using This Starter

For a new application:

1. create a project from this repository;
2. configure its development and test databases;
3. configure application secrets and administrator credentials;
4. apply migrations;
5. run the seed;
6. keep the authentication and authorization foundation;
7. add the new application's domain models and repositories;
8. build business features vertically through model, repository, service, and route layers;
9. introduce project-specific permissions when they represent real authorization requirements;
10. extend testing around the new business behavior.

The goal is to provide a strong starting point without dictating the business domain that comes next.
