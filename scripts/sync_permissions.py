from app import create_app
from app.config.database import SessionLocal
from app.permissions.sync_service import PermissionSyncService

if __name__ == "__main__":
    create_app()

    with SessionLocal() as session:
        service = PermissionSyncService(session)
        result = service.sync()

        print(f"Created: {result.created}")
        print(f"Updated: {result.updated}")
        print(f"Unchanged: {result.unchanged}")
        print(f"Stale: {result.stale}")
