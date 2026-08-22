# type: ignore
from flask import Blueprint, request

from app.auth.authorization import permission_required
from app.config.database import SessionLocal
from app.roles.schema import (
    add_permission_schema,
    create_role_schema,
    role_schema,
    roles_schema,
    update_role_schema,
)
from app.roles.service import RoleService

role_bp = Blueprint(
    "roles",
    __name__,
    url_prefix="/api/roles",
)


@role_bp.get("/")
@permission_required("role.read")
def get_roles():
    with SessionLocal() as session:
        service = RoleService(session)
        roles = service.get_roles()

        return roles_schema.dump(roles), 200


@role_bp.get("/<uuid:role_id>")
@permission_required("role.read")
def get_role(role_id):

    with SessionLocal() as session:
        service = RoleService(session)

        role = service.get_role(role_id)

        return role_schema.dump(role)


@role_bp.post("/")
@permission_required("role.create")
def create_role():

    data = create_role_schema.load(request.get_json())

    with SessionLocal() as session:
        service = RoleService(session)

        role = service.create_role(
            name=data["name"],
            description=data.get("description"),
        )

        return (
            role_schema.dump(role),
            201,
        )


@role_bp.patch("/<uuid:role_id>")
@permission_required("role.update")
def update_role(role_id):

    data = update_role_schema.load(request.get_json())

    with SessionLocal() as session:
        service = RoleService(session)

        role = service.update_role(role_id, data)

        return role_schema.dump(role)


@role_bp.delete("/<uuid:role_id>")
@permission_required("role.delete")
def delete_role(role_id):

    with SessionLocal() as session:
        service = RoleService(session)

        service.delete_role(role_id)

        return (
            {"message": "Role deleted successfully."},
            200,
        )


@role_bp.post("/<uuid:role_id>/permissions")
@permission_required("role.assign_permission")
def assign_permission(role_id):
    data = add_permission_schema.load(request.get_json())

    with SessionLocal() as session:
        service = RoleService(session)

        role = service.assign_permission(
            role_id,
            data["permission_id"],
        )

        return role_schema.dump(role), 200


@role_bp.delete("/<uuid:role_id>/permissions/<uuid:permission_id>")
@permission_required("role.assign_permission")
def remove_permission(role_id, permission_id):
    with SessionLocal() as session:
        service = RoleService(session)

        role = service.remove_permission(role_id, permission_id)

        return role_schema.dump(role), 200
