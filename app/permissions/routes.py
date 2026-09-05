from typing import Any, cast

from flask import Blueprint

from app.auth.authorization import permission_required
from app.config.database import SessionLocal
from app.permissions.schema import (
    permission_schema,
    permissions_schema,
)
from app.permissions.service import PermissionService

permission_bp = Blueprint(
    "permissions",
    __name__,
    url_prefix="/api/permissions",
)


@permission_bp.get("/")
@permission_required("permission.read")
def get_permissions():
    with SessionLocal() as session:
        service = PermissionService(session)
        permissions = service.get_permissions()
        response = cast(
            list[dict[str, Any]],
            permissions_schema.dump(permissions),
        )
        return response, 200


@permission_bp.get("/<uuid:permission_id>")
@permission_required("permission.read")
def get_permission(permission_id):

    with SessionLocal() as session:
        service = PermissionService(session)

        permission = service.get_permission(permission_id)
        response = cast(
            dict[str, Any],
            permission_schema.dump(permission),
        )

        return response, 200
