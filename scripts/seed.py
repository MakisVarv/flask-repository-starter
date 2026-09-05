import os

from sqlalchemy import select
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from app.permissions.model import Permission
from app.roles.model import Role
from app.users.model import User
from app.users.repository import UserRepository

PERMISSIONS: list[dict[str, str]] = [
    # Users
    {"name": "user.read", "description": "Read user information"},
    {"name": "user.create", "description": "Create users"},
    {"name": "user.update", "description": "Update users"},
    {"name": "user.delete", "description": "Delete users"},
    {"name": "user.change_role", "description": "Change a user's role"},
    # Roles
    {"name": "role.read", "description": "Read roles"},
    {"name": "role.create", "description": "Create roles"},
    {"name": "role.update", "description": "Update roles"},
    {"name": "role.delete", "description": "Delete roles"},
    {
        "name": "role.assign_permission",
        "description": "Assign or remove permissions from roles",
    },
    # Permissions
    {"name": "permission.read", "description": "Read permissions"},
    # Dashboard
    {"name": "dashboard.read", "description": "View dashboard"},
]
ROLES: list[dict[str, str | int]] = [
    {"name": "Admin", "description": "Full system administrator", "level": 100},
    {"name": "User", "description": "Standard system user", "level": 10},
]

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "Admin": [permission["name"] for permission in PERMISSIONS]
}


def seed_permissions(session: Session) -> None:

    print("Starting permission seed...")

    for permission in PERMISSIONS:

        print(permission["name"])

        existing = session.scalar(
            select(Permission).where(Permission.name == permission["name"])
        )

        if existing:
            print(f"{permission['name']} already exists")
            continue

        print(f"Adding {permission['name']}")

        session.add(
            Permission(name=permission["name"], description=permission["description"])
        )

    session.commit()

    print("Commit completed.")


def seed_roles(session: Session) -> None:
    print("Starting roles seed")
    for role in ROLES:

        print(role["name"])

        existing = session.scalar(select(Role).where(Role.name == role["name"]))

        if existing:
            print(f"{role['name']} already exists")
            continue

        print(f"Adding {role['name']}")

        session.add(
            Role(
                name=role["name"],
                description=role["description"],
                level=role["level"],
            )
        )

    session.commit()

    print("Commit completed.")


def seed_role_permissions(session: Session) -> None:
    print("Starting role-permission seed...")

    for role_name, permission_names in ROLE_PERMISSIONS.items():
        role = session.scalar(select(Role).where(Role.name == role_name))

        if role is None:
            raise RuntimeError(f"Role '{role_name}' does not exist.")

        existing_permissions = {permission.name for permission in role.permissions}

        for permission_name in permission_names:
            if permission_name in existing_permissions:
                print(f"{role_name} already has {permission_name}")
                continue

            permission = session.scalar(
                select(Permission).where(Permission.name == permission_name)
            )

            if permission is None:
                raise RuntimeError(f"Permission '{permission_name}' does not exist.")

            print(f"Assigning {permission_name} to {role_name}")
            role.permissions.append(permission)

    session.commit()
    print("Role-permission commit completed.")


def seed_admin(session: Session) -> None:
    print("Starting admin seed...")

    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    first_name = os.getenv("ADMIN_FIRST_NAME", "System")
    last_name = os.getenv("ADMIN_LAST_NAME", "Admin")

    if not email or not password:
        raise RuntimeError("ADMIN_EMAIL and ADMIN_PASSWORD must be configured.")
    if len(password) < 8:
        raise RuntimeError("ADMIN_PASSWORD must be at least 8 characters.")

    user_repository = UserRepository(session)

    existing = user_repository.get_by_email(email)

    admin_role = session.scalar(select(Role).where(Role.name == "Admin"))

    if admin_role is None:
        raise RuntimeError("Admin role does not exist.")

    if existing:
        if existing.role_id != admin_role.id:
            existing.role_id = admin_role.id
            session.commit()
            print("Existing user promoted to Admin.")
        else:
            print("Admin user already exists.")

        return

    password_hash = generate_password_hash(password)

    admin = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=password_hash,
        role_id=admin_role.id,
    )

    try:
        user_repository.create(admin)
        session.commit()
    except Exception:
        session.rollback()
        raise
    print("Admin user created.")


if __name__ == "__main__":
    from app import create_app
    from app.config.database import SessionLocal

    create_app()

    with SessionLocal() as session:
        seed_permissions(session)
        seed_roles(session)
        seed_role_permissions(session)
        seed_admin(session)
