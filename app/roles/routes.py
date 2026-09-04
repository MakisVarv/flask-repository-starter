import uuid
from typing import Any, cast

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity

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
from app.users.service import UserService

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
        response = cast(
            list[dict[str, Any]],
            roles_schema.dump(roles),
        )
        return response, 200


@role_bp.get("/<uuid:role_id>")
@permission_required("role.read")
def get_role(role_id):

    with SessionLocal() as session:
        service = RoleService(session)

        role = service.get_role(role_id)
        response = cast(
            dict[str, Any],
            role_schema.dump(role),
        )

        return response, 200


@role_bp.post("/")
@permission_required("role.create")
def create_role():

    data = cast(
        dict[str, Any],
        create_role_schema.load(request.get_json()),
    )
    actor_id = get_jwt_identity()
    with SessionLocal() as session:
        service = RoleService(session)
        user_service = UserService(session)
        actor = user_service.get_user(uuid.UUID(actor_id))
        role = service.create_role(
            actor,
            name=data["name"],
            description=data.get("description"),
            level=data["level"],
        )
        response = cast(
            dict[str, Any],
            role_schema.dump(role),
        )
        return (
            response,
            201,
        )


@role_bp.patch("/<uuid:role_id>")
@permission_required("role.update")
def update_role(role_id):

    data = cast(
        dict[str, Any],
        update_role_schema.load(request.get_json()),
    )
    actor_id = get_jwt_identity()
    with SessionLocal() as session:
        service = RoleService(session)
        user_service = UserService(session)
        actor = user_service.get_user(uuid.UUID(actor_id))

        role = service.update_role(actor, role_id, data)
        response = cast(
            dict[str, Any],
            role_schema.dump(role),
        )

        return response, 200


@role_bp.delete("/<uuid:role_id>")
@permission_required("role.delete")
def delete_role(role_id):
    actor_id = get_jwt_identity()
    with SessionLocal() as session:
        service = RoleService(session)
        user_service = UserService(session)
        actor = user_service.get_user(uuid.UUID(actor_id))
        service.delete_role(actor, role_id)

        return (
            {"message": "Role deleted successfully."},
            200,
        )


@role_bp.post("/<uuid:role_id>/permissions")
@permission_required("role.assign_permission")
def assign_permission(role_id):
    data = cast(
        dict[str, Any],
        add_permission_schema.load(request.get_json()),
    )
    actor_id = get_jwt_identity()
    with SessionLocal() as session:
        service = RoleService(session)
        user_service = UserService(session)
        actor = user_service.get_user(uuid.UUID(actor_id))

        role = service.assign_permission(
            actor,
            role_id,
            data["permission_id"],
        )
        response = cast(
            dict[str, Any],
            role_schema.dump(role),
        )
        return response, 200


@role_bp.delete("/<uuid:role_id>/permissions/<uuid:permission_id>")
@permission_required("role.assign_permission")
def remove_permission(role_id, permission_id):
    actor_id = get_jwt_identity()
    with SessionLocal() as session:
        service = RoleService(session)
        user_service = UserService(session)
        actor = user_service.get_user(uuid.UUID(actor_id))
        role = service.remove_permission(actor, role_id, permission_id)
        response = cast(
            dict[str, Any],
            role_schema.dump(role),
        )
        return response, 200
