import os

from sqlalchemy import select
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from app.roles.model import Role
from app.users.model import User
from app.users.repository import UserRepository

ROLES: list[dict[str, str | int]] = [
    {"name": "Admin", "description": "Full system administrator", "level": 100},
    {"name": "User", "description": "Standard system user", "level": 10},
]


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
        seed_roles(session)
        seed_admin(session)
