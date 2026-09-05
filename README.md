# Flask Repository Starter

A reusable Flask backend starter focused on **clean architecture, secure authentication, role-based authorization, and production-oriented backend fundamentals**.

Built with Flask, PostgreSQL, SQLAlchemy, Alembic, Marshmallow, and Flask-JWT-Extended.

---

## Highlights

- Repository → Service → Route architecture
- PostgreSQL with SQLAlchemy 2.x
- Alembic migrations
- JWT access tokens
- HttpOnly refresh-token cookies
- Refresh-token rotation
- Server-side authentication sessions
- Refresh-token replay detection
- Session revocation and logout
- CSRF protection for refresh cookies
- Role-based access control
- Role hierarchy and target-aware authorization
- Protected built-in roles
- Developer-defined permissions
- Runtime role-permission management
- User administration with pagination, filtering, sorting, and lifecycle rules
- PostgreSQL-backed integration tests
- Ruff and Black quality checks

---

## Architecture

The application separates responsibilities into clear layers:

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

### Routes

Routes handle HTTP concerns:

- request parsing;
- schema validation;
- authentication and authorization decorators;
- JWT identity extraction;
- response serialization;
- status codes.

### Services

Services contain application rules and transaction boundaries.

Examples:

- authentication;
- refresh-token validation;
- role hierarchy;
- user lifecycle rules;
- permission assignment;
- protected-role invariants.

### Repositories

Repositories encapsulate persistence operations and database queries.

Repositories do not own transaction commits; services coordinate application-level transactions.

---

## Project Structure

```text
.
├── app/
│   ├── auth/
│   ├── common/
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
├── alembic.ini
├── Pipfile
├── Pipfile.lock
├── pyproject.toml
├── pytest.ini
├── README.md
└── run.py
```

---

## Tech Stack

| Area                  | Technology         |
| --------------------- | ------------------ |
| Framework             | Flask              |
| ORM                   | SQLAlchemy 2.x     |
| Database              | PostgreSQL         |
| Driver                | psycopg            |
| Migrations            | Alembic            |
| Authentication        | Flask-JWT-Extended |
| Validation            | Marshmallow        |
| CORS                  | Flask-CORS         |
| Testing               | Pytest             |
| Coverage              | pytest-cov         |
| Dependency Management | Pipenv             |
| Formatting            | Black              |
| Linting               | Ruff               |

---

## Authentication

Authentication uses:

```text
Access JWT
+
Refresh JWT
+
AuthSession database record
```

### Access Tokens

Access tokens are short-lived and returned in JSON.

The frontend sends them using:

```http
Authorization: Bearer <access_token>
```

The configured lifetime is approximately 15 minutes.

### Refresh Tokens

Refresh tokens are longer-lived and stored in Secure, HttpOnly cookies.

They are:

- CSRF protected;
- rotated on successful refresh;
- unavailable to normal frontend JavaScript;
- linked to a server-side authentication session.

The configured lifetime is approximately 7 days.

---

## Server-Side Sessions

Each login creates an `AuthSession`.

The session tracks:

```text
sid
user_id
current_refresh_jti
expires_at
revoked_at
```

This allows the backend to revoke refresh access independently for each login session or device.

---

## Refresh Rotation and Replay Detection

Only the latest refresh-token `jti` is accepted for a session.

Conceptually:

```text
R1 → R2 → R3
```

Once `R1` has been exchanged for `R2`, presenting `R1` again is treated as possible replay.

The backend rejects the request and revokes the corresponding authentication session.

This invalidates the active refresh-token family instead of allowing suspicious reuse to continue.

---

## Logout

Logout:

- validates the current refresh session;
- marks the corresponding `AuthSession` as revoked;
- clears refresh cookies.

Existing short-lived access tokens are allowed to expire naturally.

---

## Authorization Model

Authorization separates two concerns:

```text
RBAC
→ WHAT may the actor do?

Hierarchy
→ WHICH TARGETS may the actor manage?
```

Named permissions determine capabilities.

Examples:

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
```

Hierarchy is then applied when an action targets another user or role.

---

## Role Hierarchy

Roles contain a numeric `level`.

Built-in roles:

```text
Admin → 100
User  → 10
```

A non-top-level actor may manage only targets below their own level.

Example:

```text
Actor 50 → Target 40 ✅
Actor 50 → Target 50 ❌
Actor 50 → Target 60 ❌
```

The same rule applies when creating or assigning role levels.

Level `100` is reserved for top authority and may manage other level-100 roles when otherwise authorized.

---

## Protected Built-In Roles

`Admin` and `User` are system roles.

They cannot be:

- deleted;
- renamed;
- assigned a different hierarchy level.

This protects system assumptions such as:

- public registration depending on the `User` role;
- `Admin` remaining the reserved level-100 authority.

Descriptions may still be edited.

---

## Permission Model

Permissions are treated as **developer-defined capabilities**.

Runtime administrators may compose roles using existing permissions, but they cannot create, rename, or delete permission definitions through the API.

Runtime Permission API:

```text
GET /api/permissions/
GET /api/permissions/<permission_id>
```

Role-permission relationships remain runtime-managed.

This keeps capability definitions aligned with application code while still allowing flexible role composition.

---

## User Management

The starter includes administrative user management with:

- pagination;
- search;
- filtering;
- sorting;
- profile updates;
- activation/deactivation;
- role assignment;
- deletion rules.

A user must be inactive before deletion.

Public registration always resolves the built-in `User` role internally and does not accept arbitrary role assignment.

---

## API Overview

### Authentication

| Method  | Endpoint             | Purpose                                         |
| ------- | -------------------- | ----------------------------------------------- |
| `POST`  | `/api/auth/register` | Register a standard user                        |
| `POST`  | `/api/auth/login`    | Authenticate and create a session               |
| `POST`  | `/api/auth/refresh`  | Rotate refresh token and issue new access token |
| `POST`  | `/api/auth/logout`   | Revoke refresh session                          |
| `GET`   | `/api/auth/me`       | Return current user                             |
| `PATCH` | `/api/auth/me`       | Update current-user profile                     |

### Users

| Method   | Endpoint                      | Permission         |
| -------- | ----------------------------- | ------------------ |
| `GET`    | `/api/users/`                 | `user.read`        |
| `GET`    | `/api/users/<user_id>`        | `user.read`        |
| `POST`   | `/api/users/`                 | `user.create`      |
| `PATCH`  | `/api/users/<user_id>`        | `user.update`      |
| `PATCH`  | `/api/users/<user_id>/status` | `user.update`      |
| `PATCH`  | `/api/users/<user_id>/role`   | `user.change_role` |
| `DELETE` | `/api/users/<user_id>`        | `user.delete`      |

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

| Method | Endpoint                           | Permission        |
| ------ | ---------------------------------- | ----------------- |
| `GET`  | `/api/permissions/`                | `permission.read` |
| `GET`  | `/api/permissions/<permission_id>` | `permission.read` |

---

## Error Responses

General application and authentication errors use:

```json
{
  "message": "..."
}
```

Validation failures expose field-level errors through:

```json
{
  "errors": {
    "field": ["Validation message."]
  }
}
```

Flask-JWT-Extended is configured to use `message` rather than its default `msg` key.

---

## Configuration

Create a `.env` file from `.env.example`.

Example:

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

Production configuration uses secure authentication cookies.

Local development and testing explicitly relax cookie security for HTTP environments.

---

## Getting Started

### Install Dependencies

```bash
pipenv install --dev
```

### Create PostgreSQL Databases

Example:

```sql
CREATE DATABASE starter_db_dev;
CREATE DATABASE starter_db_test;
```

### Apply Migrations

```bash
pipenv run alembic upgrade head
```

Apply the same migration history to the test database.

### Seed Authorization Data

```bash
pipenv run python -m scripts.seed
```

The seed initializes:

- built-in permissions;
- `Admin`;
- `User`;
- role levels;
- Admin permission assignments;
- the configured administrator account.

The seed is idempotent.

### Run the Application

```bash
pipenv run python run.py
```

Default development URL:

```text
http://127.0.0.1:5000
```

---

## Testing

Tests run against a dedicated PostgreSQL database.

```bash
pipenv run pytest
```

The suite covers the important behavioral boundaries of the starter:

- login and registration;
- refresh rotation;
- replay detection;
- logout and session revocation;
- inactive-account enforcement;
- user-management lifecycle;
- permission enforcement;
- role hierarchy;
- role-level persistence;
- role-permission hierarchy;
- protected built-in roles.

Tests use transactional isolation so each test can exercise real database behavior without permanently modifying test data.

---

## Quality Checks

```bash
pipenv run ruff check .
pipenv run black --check .
pipenv run pytest
```

These commands form the final local quality gate before committing changes.

---

## Frontend Integration

The backend is designed to support a separately deployed frontend such as React.

Recommended token handling:

```text
Access token
→ frontend memory

Refresh token
→ HttpOnly cookie
```

Normal protected requests use the access token.

After reload or access-token expiry, the frontend can call:

```text
POST /api/auth/refresh
```

with credentials enabled and the CSRF header included.

The backend validates the server-side session, rotates the refresh token, and returns a new access token.

---

## Security Characteristics

The starter includes:

- hashed passwords;
- generic login failures;
- short-lived access tokens;
- Secure HttpOnly refresh cookies;
- CSRF protection;
- refresh-token rotation;
- replay detection;
- server-side session revocation;
- inactive-account enforcement;
- database-authoritative permissions;
- role hierarchy;
- protected built-in roles;
- credentialed CORS restricted to a configured frontend origin;
- environment-based secrets.

JWT claims are signed, not encrypted, so sensitive secrets should never be stored inside token payloads.

---

## Design Goals

The project favors:

- explicit responsibility boundaries;
- readable layered architecture;
- service-owned transactions;
- database-authoritative authorization;
- permissions over hardcoded role checks;
- hierarchy only where target authorization requires it;
- small abstractions;
- real PostgreSQL integration testing;
- frontend/backend separation.

It intentionally avoids adding infrastructure or patterns without a concrete requirement.

---

## Future Direction

The most natural next extension is a **developer-controlled permission registry and synchronization process**.

That could:

- define the permission catalog in code;
- create missing database permissions;
- synchronize safe metadata;
- prevent code/database permission drift.

Permission definitions would remain developer-controlled rather than becoming runtime administrator CRUD.

---

## Summary

This starter demonstrates a reusable Flask backend foundation with:

- layered architecture;
- PostgreSQL persistence;
- secure session-based refresh-token handling;
- JWT authentication;
- replay detection;
- RBAC;
- role hierarchy;
- protected system roles;
- developer-defined permissions;
- runtime role composition;
- migrations;
- integration testing.

It is designed to be small enough to understand while still demonstrating the kinds of backend concerns expected in real full-stack applications.
