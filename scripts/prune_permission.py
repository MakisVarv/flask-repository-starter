import sys

from app import create_app
from app.config.database import SessionLocal
from app.permissions.prune_service import PermissionPruneService

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m scripts.prune_permission <permission_name>")

    permission_name = sys.argv[1]

    create_app()

    with SessionLocal() as session:
        service = PermissionPruneService(session)
        service.prune(permission_name)

    print(f"Pruned permission: {permission_name}")
