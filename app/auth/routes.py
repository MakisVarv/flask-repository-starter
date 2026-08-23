import uuid
from typing import Any, cast

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    get_jwt,
    get_jwt_identity,
    jwt_required,
    set_refresh_cookies,
)

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

        user, access_token, refresh_token = service.login(
            email=data["email"],
            password=data["password"],
        )
        user_response = cast(
            dict[str, Any],
            user_schema.dump(user),
        )
        response = jsonify(
            {
                "access_token": access_token,
                "user": user_response,
            }
        )
        set_refresh_cookies(response, refresh_token)
        return response, 200


@auth_bp.post("/refresh")
@jwt_required(refresh=True, locations=["cookies"])
def refresh():
    user_id = uuid.UUID(get_jwt_identity())

    claims = get_jwt()

    sid = uuid.UUID(claims["sid"])
    refresh_jti = claims["jti"]
    with SessionLocal() as session:
        service = AuthService(session)
        new_access_token, new_refresh_token = service.refresh(
            user_id=user_id,
            sid=sid,
            refresh_jti=refresh_jti,
        )
        response = jsonify(
            {
                "access_token": new_access_token,
            }
        )
        set_refresh_cookies(response, new_refresh_token)
        return response, 200


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
