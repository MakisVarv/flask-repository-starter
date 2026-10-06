from app import create_app
from app.config.config import DevelopmentConfig
from app.config.database import SessionLocal
from app.permissions.sync_service import PermissionSyncService

app = create_app(DevelopmentConfig)
if __name__ == "__main__":
    with SessionLocal() as session:
        result = PermissionSyncService(session).sync()

        if result.stale:
            raise RuntimeError(f"Stale permissions detected: {', '.join(result.stale)}")
    app.run(debug=True)
