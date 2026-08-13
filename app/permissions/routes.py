# type: ignore
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

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
@jwt_required()
@permission_required("permission.read")
def get_permissions():
    with SessionLocal() as session:
        service = PermissionService(session)
        permissions = service.get_permissions()

        return permissions_schema.dump(permissions), 200


@permission_bp.get("/<uuid:permission_id>")
@jwt_required()
@permission_required("permission.read")
def get_permission(permission_id):

    with SessionLocal() as session:
        service = PermissionService(session)

        permission = service.get_permission(permission_id)

        return permission_schema.dump(permission)


@permission_bp.post("/")
@jwt_required()
@permission_required("permission.create")
def create_permission():

    data = create_permission_schema.load(request.get_json())

    with SessionLocal() as session:
        service = PermissionService(session)

        permission = service.create_permission(
            name=data["name"],
            description=data.get("description"),
        )

        return (
            permission_schema.dump(permission),
            201,
        )


@permission_bp.patch("/<uuid:permission_id>")
@jwt_required()
@permission_required("permission.update")
def update_permission(permission_id):

    data = update_permission_schema.load(request.get_json())

    with SessionLocal() as session:
        service = PermissionService(session)

        permission = service.update_permission(permission_id, data)

        return permission_schema.dump(permission)


@permission_bp.delete("/<uuid:permission_id>")
@jwt_required()
@permission_required("permission.delete")
def delete_permission(permission_id):

    with SessionLocal() as session:
        service = PermissionService(session)

        service.delete_permission(permission_id)

        return (
            {"message": "Permission deleted successfully."},
            200,
        )
