from typing import Any, cast

from flask import Blueprint, request

from app.auth.authorization import permission_required
from app.config.database import SessionLocal
from app.permissions.schema import (
    create_permission_schema,
    permission_schema,
    permissions_schema,
    update_permission_schema,
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


@permission_bp.post("/")
@permission_required("permission.create")
def create_permission():

    data = cast(
        dict[str, Any],
        create_permission_schema.load(request.get_json()),
    )
    with SessionLocal() as session:
        service = PermissionService(session)

        permission = service.create_permission(
            name=data["name"],
            description=data.get("description"),
        )
        response = cast(
            dict[str, Any],
            permission_schema.dump(permission),
        )

        return (
            response,
            201,
        )


@permission_bp.patch("/<uuid:permission_id>")
@permission_required("permission.update")
def update_permission(permission_id):

    data = cast(
        dict[str, Any],
        update_permission_schema.load(request.get_json()),
    )
    with SessionLocal() as session:
        service = PermissionService(session)

        permission = service.update_permission(permission_id, data)
        response = cast(
            dict[str, Any],
            permission_schema.dump(permission),
        )
        return response, 200


@permission_bp.delete("/<uuid:permission_id>")
@permission_required("permission.delete")
def delete_permission(permission_id):

    with SessionLocal() as session:
        service = PermissionService(session)

        service.delete_permission(permission_id)

        return (
            {"message": "Permission deleted successfully."},
            200,
        )
