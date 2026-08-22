import uuid
from typing import Any, cast

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.auth.schema import login_schema, register_schema, update_me_schema
from app.auth.service import AuthService
from app.config.database import SessionLocal
from app.users.schema import user_schema

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth",
)


@auth_bp.post("/register")
def register():
    data = cast(
        dict[str, Any],
        register_schema.load(request.get_json()),
    )
    with SessionLocal() as session:
        service = AuthService(session)

        user = service.register(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            password=data["password"],
            phone=data.get("phone"),
        )
        response = cast(
            dict[str, Any],
            user_schema.dump(user),
        )

        return response, 201


@auth_bp.post("/login")
def login():

    data = cast(
        dict[str, Any],
        login_schema.load(request.get_json()),
    )
    with SessionLocal() as session:
        service = AuthService(session)

        user, access_token = service.login(
            email=data["email"],
            password=data["password"],
        )
        user_response = cast(
            dict[str, Any],
            user_schema.dump(user),
        )
        return {
            "access_token": access_token,
            "user": user_response,
        }, 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = uuid.UUID(get_jwt_identity())

    with SessionLocal() as session:
        service = AuthService(session)
        user = service.get_current_user(user_id)

        response = cast(
            dict[str, Any],
            user_schema.dump(user),
        )
        return response, 200


@auth_bp.patch("/me")
@jwt_required()
def update_me():
    user_id = uuid.UUID(get_jwt_identity())
    data = cast(
        dict[str, Any],
        update_me_schema.load(request.get_json()),
    )

    with SessionLocal() as session:
        service = AuthService(session)
        user = service.update_current_user(user_id, data)

        response = cast(
            dict[str, Any],
            user_schema.dump(user),
        )
        return response, 200
