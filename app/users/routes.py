from typing import Any, cast

from flask import Blueprint, request

from app.auth.authorization import permission_required
from app.config.database import SessionLocal
from app.users.schema import (
    assign_role_schema,
    create_user_schema,
    update_user_schema,
    user_query_schema,
    user_schema,
    user_status_schema,
    users_schema,
)
from app.users.service import UserService

user_bp = Blueprint("users", __name__, url_prefix="/api/users")


@user_bp.get("/")
@permission_required("user.read")
def get_users():
    query = cast(
        dict[str, Any],
        user_query_schema.load(request.args),
    )

    page = query["page"]
    page_size = query["page_size"]
    search = query["search"]
    role = query["role"]
    is_active = query["is_active"]
    sort = query["sort"]
    with SessionLocal() as session:
        service = UserService(session)
        users, pagination = service.get_users(
            page=page,
            page_size=page_size,
            search=search,
            sort=sort,
            role=role,
            is_active=is_active,
        )

        return {
            "items": users_schema.dump(users),
            "pagination": pagination,
        }, 200


@user_bp.get("/<uuid:user_id>")
@permission_required("user.read")
def get_user(user_id):

    with SessionLocal() as session:
        service = UserService(session)

        user = service.get_user(user_id)

        response = cast(
            dict[str, Any],
            user_schema.dump(user),
        )

        return response, 200


@user_bp.post("/")
@permission_required("user.create")
def create_user():
    data = cast(
        dict[str, Any],
        create_user_schema.load(request.get_json()),
    )

    with SessionLocal() as session:
        service = UserService(session)

        user = service.create_user(**data)

        response = cast(
            dict[str, Any],
            user_schema.dump(user),
        )

        return response, 201


@user_bp.patch("/<uuid:user_id>")
@permission_required("user.update")
def update_user(user_id):
    data = cast(
        dict[str, Any],
        update_user_schema.load(request.get_json()),
    )

    with SessionLocal() as session:
        service = UserService(session)
        user = service.update_user(user_id, data)

        response = cast(
            dict[str, Any],
            user_schema.dump(user),
        )

        return response, 200


@user_bp.patch("/<uuid:user_id>/status")
@permission_required("user.update")
def change_user_status(user_id):
    data = cast(
        dict[str, Any],
        user_status_schema.load(request.get_json()),
    )
    with SessionLocal() as session:
        service = UserService(session)
        user = service.change_status(
            user_id,
            data["is_active"],
        )
        response = cast(
            dict[str, Any],
            user_schema.dump(user),
        )
    return response, 200


@user_bp.delete("/<uuid:user_id>")
@permission_required("user.delete")
def delete_user(user_id):

    with SessionLocal() as session:
        service = UserService(session)

        service.delete_user(user_id)

        return (
            {"message": "User deleted successfully."},
            204,
        )


@user_bp.patch("/<uuid:user_id>/role")
@permission_required("user.change_role")
def change_role(user_id):
    data = cast(
        dict[str, Any],
        assign_role_schema.load(request.get_json()),
    )

    with SessionLocal() as session:
        service = UserService(session)

        user = service.change_role(user_id, data["role_id"])

        response = cast(
            dict[str, Any],
            user_schema.dump(user),
        )

        return response, 200
