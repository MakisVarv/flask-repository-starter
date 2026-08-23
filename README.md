# Flask Repository Starter

A reusable backend starter for building serious Flask applications with a clean **Repository → Service → Route** architecture, PostgreSQL persistence, JWT authentication, refresh-token rotation, session revocation, CORS support, and role/permission-based authorization.

The project is intentionally small and domain-agnostic. It provides the infrastructure that many real applications need before business-specific features are added.

## Why This Project Exists

Starting a new backend often means rebuilding the same foundation:

- application configuration;
- database sessions;
- authentication;
- authorization;
- validation;
- migrations;
- error handling;
- testing;
- frontend/API integration.

This repository keeps that foundation in one focused project so it can be:

- used as a starting point for future Flask applications;
- extended without carrying unrelated business-domain code;
- connected to standalone frontend applications such as React;
- used to practice testing, tooling, CI/CD, deployment, and other engineering concerns in isolation;
- used as a reference implementation for layered Python backend architecture.

## Features

- Flask application factory
- Development, testing, and production-safe configuration
- PostgreSQL database
- SQLAlchemy 2.x ORM
- Repository pattern for persistence
- Service layer for application logic
- Service-owned transaction boundaries
- Marshmallow request/response validation
- JWT authentication with Flask-JWT-Extended
- Short-lived access tokens
- HttpOnly refresh-token cookies
- Refresh-token rotation
- Server-side authentication sessions
- Refresh-token replay detection
- Session revocation
- CSRF protection for cookie-based refresh operations
- Login and logout flows
- User registration
- Current-user profile viewing and editing
- Role-based access model
- Fine-grained permissions
- User, role, and permission management
- User pagination, search, and filtering
- Role-permission assignment
- Active-account enforcement
- CORS configuration for a separate frontend application
- Centralized application error handling
- Timestamp mixin for persistent entities
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
| PostgreSQL Driver          | psycopg            |
| Migrations                 | Alembic            |
| Authentication             | Flask-JWT-Extended |
| CORS                       | Flask-CORS         |
| Validation / Serialization | Marshmallow        |
| Testing                    | Pytest             |
| Coverage                   | pytest-cov         |
| Environment Configuration  | python-dotenv      |
| Dependency Management      | Pipenv             |
| Formatting                 | Black              |
| Linting                    | Ruff               |

## Architecture

The application separates responsibilities into four main layers.

### Routes

Routes handle HTTP concerns such as:

- request parsing;
- authentication and authorization decorators;
- extracting JWT identity and claims;
- setting and clearing authentication cookies;
- response payloads;
- HTTP status codes.

### Services

Services contain application rules and coordinate operations across repositories.

They are responsible for concerns such as:

- authentication behavior;
- token-session validation;
- refresh-token rotation;
- session revocation;
- user-management rules;
- transaction boundaries.

### Repositories

Repositories encapsulate database queries and persistence operations.

Repositories do **not** own transaction commits. Transaction boundaries remain in the service layer.

### Models

Models define SQLAlchemy entities and relationships.

The normal request flow is:

```text
HTTP Request
    ↓
Route
    ↓
Service
    ↓
Repository
    ↓
SQLAlchemy
    ↓
PostgreSQL
```

This keeps HTTP, application logic, and persistence concerns from becoming tightly coupled and makes the project easier to extend and test.

## Project Structure

```text
.
├── app/
│   ├── auth/
│   │   ├── authorization.py
│   │   ├── model.py
│   │   ├── repository.py
│   │   ├── routes.py
│   │   ├── schema.py
│   │   └── service.py
│   ├── common/
│   │   ├── exceptions/
│   │   └── error_handler.py
│   ├── config/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── extensions.py
│   │   └── mixins.py
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
├── pyproject.toml
├── pytest.ini
├── README.md
└── run.py
```

## Core Domain

The starter contains four generic infrastructure entities.

### User

Represents an authenticated application account.

A user:

- has account information;
- has an active/inactive state;
- belongs to a role;
- can own multiple authentication sessions.

### Role

Groups permissions and can be assigned to users.

### Permission

Represents an application action that a role may perform.

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

### AuthSession

Represents one authenticated login session.

For example, a user's laptop login and phone login can be represented by separate authentication sessions.

An authentication session tracks information such as:

```text
id / sid
user_id
current_refresh_jti
expires_at
revoked_at
```

This allows the backend to maintain control over long-lived refresh credentials while keeping access tokens short-lived.

## Roles and Permissions

The seed currently creates two baseline roles.

### Admin

Receives all seeded administrative permissions.

### User

The default standard-user role.

It intentionally receives no broad administrative user-management permissions.

Self-service behavior such as viewing or editing one's own profile is handled separately through authenticated identity and ownership rules rather than by granting broad permissions such as `user.update`.

This keeps:

```text
administrative authorization
```

separate from:

```text
self-service ownership behavior
```

## Authentication Architecture

Authentication uses a hybrid token architecture:

```text
Access JWT
+
Refresh JWT
+
AuthSession database record
```

### Access Token

The access token is:

- short-lived;
- returned in the login or refresh JSON response;
- intended to be stored by the frontend in memory;
- sent to protected API endpoints using the `Authorization` header.

Example:

```http
Authorization: Bearer <access_token>
```

The configured access-token lifetime is approximately 15 minutes.

### Refresh Token

The refresh token is:

- longer-lived;
- stored in an HttpOnly cookie;
- automatically sent by the browser to authentication endpoints;
- unavailable to normal frontend JavaScript;
- CSRF protected;
- rotated whenever `/api/auth/refresh` succeeds.

The configured refresh-token lifetime is approximately 7 days.

### `sid`

`sid` identifies the authentication session.

Conceptually:

```text
User logs in on laptop
    ↓
sid = session-123

User logs in on phone
    ↓
sid = session-456
```

Tokens created for one login session keep the same `sid`.

### `jti`

`jti` identifies one specific JWT.

Refresh tokens belonging to the same authentication session therefore look conceptually like:

```text
sid = session-123
jti = token-A
```

After rotation:

```text
sid = session-123
jti = token-B
```

The `sid` stays the same because it is still the same login session.

The `jti` changes because a new refresh token was issued.

The database stores only the current accepted refresh-token `jti`.

## Login Flow

A successful login performs the following flow:

```text
email + password
    ↓
credentials validated
    ↓
new sid generated
    ↓
access token created
    ↓
refresh token created
    ↓
AuthSession created
    ↓
current refresh jti stored
    ↓
access token returned in JSON
    ↓
refresh token stored in HttpOnly cookie
```

The access token created directly from password authentication is marked as a fresh token.

The login response also returns the authenticated user's serialized data.

## Refresh Flow

A frontend can lose its in-memory access token when the page reloads.

The refresh cookie survives that reload.

The frontend can therefore call:

```text
POST /api/auth/refresh
```

to restore authentication.

The backend validates:

```text
refresh JWT signature
        ↓
session exists?
        ↓
session revoked?
        ↓
session expired?
        ↓
token jti matches current_refresh_jti?
        ↓
token user owns the session?
        ↓
user still exists and is active?
```

If all checks succeed:

```text
refresh token A
    ↓
new access token
+
refresh token B
    ↓
database:
current_refresh_jti A → B
```

The browser receives the new refresh cookie and the frontend receives the new access token.

This keeps the user authenticated without storing a long-lived access token in browser storage.

## Refresh-Token Rotation and Replay Detection

Refresh tokens are single-current-token credentials.

For example:

```text
R1
 ↓ refresh
R2
 ↓ refresh
R3
```

After `R1` is exchanged for `R2`, `R1` is no longer the current refresh token.

If an old token is later presented:

```text
token jti = R1
database jti = R2
```

the mismatch indicates possible token replay.

The request is rejected and the associated authentication session is revoked.

Conceptually:

```text
R1 → R2

R1 reused
    ↓
replay detected
    ↓
AuthSession revoked
    ↓
R2 also becomes unusable
```

This prevents continued use of a refresh-token family after suspicious reuse is detected.

## Logout Flow

Logout uses the current refresh token to identify the authentication session.

```text
POST /api/auth/logout
    ↓
refresh JWT validated
    ↓
sid + user_id + jti extracted
    ↓
AuthSession validated
    ↓
revoked_at set
    ↓
transaction committed
    ↓
refresh cookies removed
```

Removing the browser cookie alone would only be client-side cleanup.

Setting `revoked_at` provides the server-side security guarantee that the session can no longer be refreshed.

Existing short-lived access tokens are allowed to expire naturally.

## CSRF Protection

The refresh token is stored in a cookie, which means the browser sends it automatically.

Cookie-authenticated state-changing requests therefore require CSRF protection.

Flask-JWT-Extended's cookie CSRF protection is enabled:

```text
JWT_COOKIE_CSRF_PROTECT = True
```

Refresh and logout requests use a double-submit-style CSRF flow.

The browser sends:

```text
refresh token
→ HttpOnly cookie
```

and the frontend sends the matching CSRF value using:

```http
X-CSRF-TOKEN: <csrf_token>
```

The refresh credential itself remains inaccessible to frontend JavaScript.

## CORS

The backend is designed to support a separately hosted frontend application.

For local development, a React/Vite frontend may run at:

```text
http://localhost:5173
```

while Flask runs at:

```text
http://127.0.0.1:5000
```

These are separate origins, so CORS must explicitly allow the frontend.

The application configures Flask-CORS for API routes:

```python
cors.init_app(
    app,
    resources={
        r"/api/*": {
            "origins": app.config["FRONTEND_ORIGIN"],
        }
    },
    supports_credentials=True,
)
```

`supports_credentials=True` is required because the browser must send the refresh-token cookie to the backend.

The frontend origin is configured through:

```env
FRONTEND_ORIGIN=http://localhost:5173
```

The application does not use a wildcard origin for credentialed requests.

## Authentication and Authorization

Authentication and authorization are intentionally separate concerns.

### Authentication

Authentication answers:

```text
Who is making this request?
```

A valid access JWT provides the authenticated identity.

Authentication-only endpoints such as:

```text
GET /api/auth/me
PATCH /api/auth/me
```

use that identity to resolve the current user.

### Authorization

Authorization answers:

```text
Is this user allowed to perform this action?
```

Administrative routes use named permissions.

Permission-protected routes:

```text
verify access JWT
    ↓
resolve current user from database
    ↓
verify account state
    ↓
resolve role permissions
    ↓
allow or reject action
```

This means account and authorization changes continue to take effect after a token has been issued.

For example, if an account becomes inactive, an otherwise valid access token can no longer be used to access authenticated application functionality.

The authorization model avoids hardcoded checks such as:

```python
if user.role.name == "Admin":
    ...
```

Instead, routes depend on permissions such as:

```text
user.read
role.update
permission.create
```

New roles can therefore be introduced by assigning permissions instead of rewriting route logic.

## Administrative vs Self-Service Access

Administrative user-management routes and self-service routes are deliberately separate.

For example:

```text
GET /api/users/<user_id>
```

requires:

```text
user.read
```

even when a user requests their own ID.

Self-service access instead belongs to:

```text
GET /api/auth/me
PATCH /api/auth/me
```

This keeps ownership-based behavior separate from administrative authorization.

## Configuration

Configuration is split according to environment.

### Base Config

The base configuration uses production-safe cookie behavior:

```text
JWT_COOKIE_SECURE = True
```

This requires HTTPS for authentication cookies.

### DevelopmentConfig

Local development explicitly allows cookies over local HTTP:

```text
JWT_COOKIE_SECURE = False
```

`run.py` starts the application using `DevelopmentConfig`.

### TestingConfig

The testing configuration:

- enables Flask testing mode;
- uses `TEST_DATABASE_URL`;
- disables secure-cookie enforcement for the Flask test client.

This keeps insecure local/testing behavior explicit instead of making it the production default.

## Getting Started

### Prerequisites

You will need:

- Python 3.14
- Pipenv
- PostgreSQL

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd flask-repository-starter
```

### 2. Install Dependencies

```bash
pipenv install --dev
```

### 3. Create PostgreSQL Databases

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

### 4. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Then provide your local values:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/starter_db_dev
TEST_DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/starter_db_test

JWT_SECRET_KEY=YOUR_SECURE_RANDOM_SECRET

FRONTEND_ORIGIN=http://localhost:5173

ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=CHANGE_ME
ADMIN_FIRST_NAME=System
ADMIN_LAST_NAME=Admin
```

`ADMIN_PASSWORD` must contain at least 8 characters.

Generate a strong random value for `JWT_SECRET_KEY`.

Never commit the real `.env` file.

### 5. Apply Database Migrations

Apply the current schema to the development database:

```bash
pipenv run alembic upgrade head
```

The test database must also have the current Alembic migrations applied before running the test suite.

### 6. Seed Authorization Data

```bash
pipenv run python -m scripts.seed
```

The seed:

- creates the baseline permissions;
- creates the `Admin` and `User` roles;
- assigns all seeded permissions to `Admin`;
- creates the configured administrator account;
- promotes an existing account with `ADMIN_EMAIL` to the `Admin` role when necessary.

The seed is designed to be idempotent and can be run repeatedly without recreating existing roles, permissions, or users.

### 7. Start the Application

```bash
pipenv run python run.py
```

The development server will normally be available at:

```text
http://127.0.0.1:5000
```

## API Overview

### Authentication

| Method  | Endpoint             | Purpose                                                          |
| ------- | -------------------- | ---------------------------------------------------------------- |
| `POST`  | `/api/auth/register` | Register a standard user                                         |
| `POST`  | `/api/auth/login`    | Authenticate, return an access token, and set the refresh cookie |
| `POST`  | `/api/auth/refresh`  | Rotate the refresh token and return a new access token           |
| `POST`  | `/api/auth/logout`   | Revoke the authentication session and clear refresh cookies      |
| `GET`   | `/api/auth/me`       | Return the authenticated user                                    |
| `PATCH` | `/api/auth/me`       | Update the authenticated user's profile                          |

### Register

```text
POST /api/auth/register
```

Creates a standard user assigned to the default `User` role.

### Login

```text
POST /api/auth/login
```

Returns:

```json
{
  "access_token": "...",
  "user": {}
}
```

The response also sets the refresh-token and CSRF cookies.

### Refresh

```text
POST /api/auth/refresh
```

Authentication requirements:

```text
refresh JWT cookie
+
X-CSRF-TOKEN header
```

Returns:

```json
{
  "access_token": "..."
}
```

The refresh-token cookie is rotated as part of the response.

### Logout

```text
POST /api/auth/logout
```

Authentication requirements:

```text
refresh JWT cookie
+
X-CSRF-TOKEN header
```

The authentication session is revoked and the refresh cookies are cleared.

### Current User

```text
GET /api/auth/me
PATCH /api/auth/me
```

These endpoints use the access token:

```http
Authorization: Bearer <access_token>
```

The update endpoint allows self-service fields such as:

- first name;
- last name;
- phone.

It does not grant general user-management privileges.

## Users

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

## Roles

| Method   | Endpoint                                           | Permission               |
| -------- | -------------------------------------------------- | ------------------------ |
| `GET`    | `/api/roles/`                                      | `role.read`              |
| `GET`    | `/api/roles/<role_id>`                             | `role.read`              |
| `POST`   | `/api/roles/`                                      | `role.create`            |
| `PATCH`  | `/api/roles/<role_id>`                             | `role.update`            |
| `DELETE` | `/api/roles/<role_id>`                             | `role.delete`            |
| `POST`   | `/api/roles/<role_id>/permissions`                 | `role.assign_permission` |
| `DELETE` | `/api/roles/<role_id>/permissions/<permission_id>` | `role.assign_permission` |

## Permissions

| Method   | Endpoint                           | Permission          |
| -------- | ---------------------------------- | ------------------- |
| `GET`    | `/api/permissions/`                | `permission.read`   |
| `GET`    | `/api/permissions/<permission_id>` | `permission.read`   |
| `POST`   | `/api/permissions/`                | `permission.create` |
| `PATCH`  | `/api/permissions/<permission_id>` | `permission.update` |
| `DELETE` | `/api/permissions/<permission_id>` | `permission.delete` |

## Database and Transaction Boundaries

The project uses explicit SQLAlchemy sessions.

Repositories are responsible for persistence operations such as:

- querying;
- adding entities;
- updating entities;
- deleting entities;
- flushing and refreshing when necessary.

Repositories do not own transaction commits.

Services coordinate application operations and own transaction boundaries.

For example:

```text
Route
    ↓
Service
    ↓
multiple repository operations
    ↓
commit once
```

This keeps transactions aligned with application operations rather than individual persistence methods.

## Timestamps

Reusable entity timestamps are provided through a `TimestampMixin`.

Entities that require lifecycle tracking can inherit fields such as:

```text
created_at
updated_at
```

This avoids duplicating timestamp definitions across models while keeping the SQLAlchemy base itself domain-neutral.

## Database Migrations

Database schema changes are managed with Alembic.

After changing SQLAlchemy models:

```bash
pipenv run alembic revision --autogenerate -m "describe the change"
```

Always inspect generated migrations before applying them.

Then run:

```bash
pipenv run alembic upgrade head
```

The application does not rely on automatic table creation at startup.

Schema evolution should happen through migrations.

## Testing

The project uses Pytest with a dedicated PostgreSQL test database configured through:

```env
TEST_DATABASE_URL
```

The test database must have the current Alembic migrations applied before running the suite.

Run all tests with:

```bash
pipenv run pytest
```

The test infrastructure wraps each test in a database transaction and rolls that transaction back afterward.

This allows tests to exercise real PostgreSQL and SQLAlchemy behavior while remaining isolated from one another.

The suite covers behavior including:

- registration;
- duplicate-email protection;
- validation failures;
- successful login;
- invalid credentials;
- access-token authentication;
- invalid JWT rejection;
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
- query validation;
- refresh-token issuance;
- refresh-token rotation;
- rejection of reused refresh tokens;
- refresh-token replay detection;
- authentication-session revocation after replay;
- logout;
- refresh-cookie removal;
- server-side logout revocation;
- rejection of refresh attempts from revoked sessions;
- rejection of refresh attempts from inactive users.

Coverage reporting is configured through `pytest.ini` using `pytest-cov`.

Running the suite generates terminal coverage information and an HTML report in:

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

A simple local quality check is therefore:

```bash
pipenv run ruff check .
pipenv run black --check .
pipenv run pytest
```

## Frontend Integration

The backend is designed to work with a separate frontend client.

For a React application, the intended flow is:

```text
React
    ↓ login
Flask
    ↓
access token returned in JSON
refresh token stored as HttpOnly cookie
    ↓
React stores access token in memory
```

Normal API calls:

```text
React
    ↓
Authorization: Bearer <access_token>
    ↓
Flask API
```

When the access token is missing or expires:

```text
React
    ↓
POST /api/auth/refresh
    ↓
browser automatically sends refresh cookie
React sends CSRF header
    ↓
Flask rotates refresh token
    ↓
new access token returned
    ↓
React remains authenticated
```

The frontend HTTP client must allow credentials when communicating with the backend.

For example, an Axios client would use credentialed requests so the browser can send authentication cookies.

The access token should remain separate from the refresh cookie:

```text
access token
→ frontend memory

refresh token
→ HttpOnly browser cookie
```

## Security Characteristics

This starter deliberately applies several authentication safeguards:

- passwords are stored as hashes rather than plaintext;
- login errors do not reveal whether an email exists;
- access tokens are short-lived;
- refresh tokens are kept out of frontend JavaScript;
- refresh cookies are HttpOnly;
- production cookies use the Secure flag;
- cookie-authenticated refresh operations use CSRF protection;
- refresh tokens rotate after successful use;
- only the latest refresh-token `jti` is accepted;
- refresh-token replay revokes the associated authentication session;
- logout performs server-side revocation;
- inactive accounts cannot continue using authenticated functionality;
- authorization permissions remain database-authoritative;
- credentialed CORS is limited to the configured frontend origin;
- secrets are loaded from environment variables.

JWT payloads are signed, not encrypted, so sensitive secrets should never be placed inside JWT claims.

## Design Goals

This starter deliberately favors:

- clear responsibility boundaries over large framework abstractions;
- explicit SQLAlchemy session handling;
- repository-based persistence;
- service-owned transaction boundaries;
- reusable authentication infrastructure;
- short-lived access credentials;
- controlled long-lived refresh sessions;
- permission-based authorization instead of hardcoded role checks;
- ownership-aware self-service endpoints;
- explicit configuration by environment;
- small, understandable layers;
- migrations instead of automatic table creation;
- isolated integration testing against PostgreSQL;
- frontend/backend separation;
- domain independence.

It is **not** intended to contain every feature a Flask application could need.

Business-domain models, background jobs, caching, external integrations, queues, scheduled jobs, and other infrastructure should be added only when a real project requires them.

The starter provides a foundation rather than attempting to predict every future application's architecture.

## Possible Future Improvements

Useful engineering extensions may include:

- pre-commit hooks;
- Docker development setup;
- GitHub Actions CI;
- automated lint and test checks;
- deployment configuration;
- structured logging;
- rate limiting;
- session-management endpoints for viewing and revoking individual devices;
- absolute refresh-session lifetime policies;
- concurrency-safe refresh rotation for highly distributed deployments;
- asymmetric JWT signing for independently verifying services;
- JWT issuer and audience validation for multi-service systems;
- OAuth 2.0 / OpenID Connect integration when external identity providers are required.

These are intentionally not included merely to increase architectural complexity.

They should be introduced when a real application's requirements justify them.

## Using This Starter

For a new application:

1. create a project from this repository;
2. configure development and test databases;
3. configure application secrets;
4. configure the frontend origin;
5. configure administrator credentials;
6. apply migrations;
7. run the seed;
8. keep the authentication and authorization foundation;
9. add the application's domain models and repositories;
10. build business features vertically through model, repository, service, and route layers;
11. add project-specific permissions when they represent real authorization requirements;
12. add ownership checks where resources belong to individual users;
13. extend testing around the new business behavior;
14. add infrastructure only when the application's requirements justify it.

## Summary

This repository provides a reusable Flask backend foundation with:

```text
Flask
+
PostgreSQL
+
SQLAlchemy
+
Repository Pattern
+
Service Layer
+
JWT Access Tokens
+
HttpOnly Refresh Tokens
+
Refresh Rotation
+
Replay Detection
+
Server-Side Session Revocation
+
CSRF Protection
+
CORS
+
Roles and Permissions
+
Alembic
+
Pytest
```

It is intended to be a clean starting point for real applications while remaining small enough to understand, modify, and extend.
