# type: ignore
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.auth.authorization import permission_required

from app.config.database import SessionLocal
from app.users.schema import (
    assign_role_schema,
    create_user_schema,
    update_user_schema,
    user_schema,
    users_schema,
)
from app.users.service import UserService

user_bp = Blueprint("users", __name__, url_prefix="/api/users")


@user_bp.get("/")
@jwt_required()
@permission_required("user.read")
def get_users():
    with SessionLocal() as session:
        service = UserService(session)
        users = service.get_users()

        return users_schema.dump(users), 200


@user_bp.get("/<uuid:user_id>")
@jwt_required()
@permission_required("user.read")
def get_user(user_id):

    with SessionLocal() as session:
        service = UserService(session)

        user = service.get_user(user_id)

        return user_schema.dump(user)


@user_bp.post("/")
@jwt_required()
@permission_required("user.create")
def create_user():
    data = create_user_schema.load(request.get_json())

    with SessionLocal() as session:
        service = UserService(session)

        user = service.create_user(**data)

        return (
            user_schema.dump(user),
            201,
        )


@user_bp.patch("/<uuid:user_id>")
@jwt_required()
@permission_required("user.update")
def update_user(user_id):
    data = update_user_schema.load(request.get_json())

    with SessionLocal() as session:
        service = UserService(session)

        user = service.update_user(user_id, data)

        return user_schema.dump(user)


@user_bp.delete("/<uuid:user_id>")
@jwt_required()
@permission_required("user.delete")
def delete_user(user_id):

    with SessionLocal() as session:
        service = UserService(session)

        service.delete_user(user_id)

        return (
            {"message": "User deleted successfully."},
            200,
        )


@user_bp.patch("/<uuid:user_id>/role")
@jwt_required()
@permission_required("user.change_role")
def change_role(user_id):
    data = assign_role_schema.load(request.get_json())
    with SessionLocal() as session:
        service = UserService(session)

        user = service.change_role(user_id, data["role_id"])

        return user_schema.dump(user)
