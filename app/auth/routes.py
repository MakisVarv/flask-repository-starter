import uuid
from typing import Any, cast

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    get_jwt,
    get_jwt_identity,
    jwt_required,
    set_refresh_cookies,
    unset_refresh_cookies,
)

from app.auth.password_reset.password_reset_smtp_mailer import SMTPPasswordResetMailer
from app.auth.schema import (
    change_email_schema,
    change_password_schema,
    forgot_password_schema,
    login_schema,
    register_schema,
    reset_password_schema,
    update_me_schema,
)
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


@auth_bp.post("/logout")
@jwt_required(refresh=True, locations=["cookies"])
def logout():
    user_id = uuid.UUID(get_jwt_identity())
    claims = get_jwt()

    sid = uuid.UUID(claims["sid"])
    refresh_jti = claims["jti"]

    with SessionLocal() as session:
        service = AuthService(session)

        service.logout(
            user_id=user_id,
            sid=sid,
            refresh_jti=refresh_jti,
        )

        response = jsonify({"message": "Logged out successfully."})

        unset_refresh_cookies(response)

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


@auth_bp.post("/change-password")
@jwt_required(fresh=True)
def change_password():
    user_id = uuid.UUID(get_jwt_identity())
    data = cast(
        dict[str, Any],
        change_password_schema.load(request.get_json()),
    )
    with SessionLocal() as session:
        service = AuthService(session)
        service.change_password(
            user_id=user_id,
            current_password=data["current_password"],
            new_password=data["new_password"],
        )
        response = jsonify({"message": "Password changed successfully."})
        unset_refresh_cookies(response)
        return response, 200


@auth_bp.post("/change-email")
@jwt_required(fresh=True)
def change_email():
    user_id = uuid.UUID(get_jwt_identity())
    data = cast(
        dict[str, Any],
        change_email_schema.load(request.get_json()),
    )
    with SessionLocal() as session:
        service = AuthService(session)
        service.change_email(
            user_id=user_id,
            current_password=data["current_password"],
            new_email=data["new_email"],
        )
        response = jsonify({"message": "Email changed successfully."})
        unset_refresh_cookies(response)
        return response, 200


@auth_bp.post("/logout-all")
@jwt_required(fresh=True)
def logout_all():
    user_id = uuid.UUID(get_jwt_identity())
    with SessionLocal() as session:
        service = AuthService(session)
        service.logout_all(user_id=user_id)
        response = jsonify({"message": "Logged out from all sessions successfully."})
        unset_refresh_cookies(response)
        return response, 200


@auth_bp.post("/forgot-password")
def forgot_password():
    data = cast(
        dict[str, Any],
        forgot_password_schema.load(request.get_json()),
    )
    mailer = SMTPPasswordResetMailer(
        host=current_app.config["MAIL_HOST"],
        port=current_app.config["MAIL_PORT"],
        sender=current_app.config["MAIL_FROM"],
        frontend_origin=current_app.config["FRONTEND_ORIGIN"],
        username=current_app.config["MAIL_USERNAME"],
        password=current_app.config["MAIL_PASSWORD"],
        use_tls=current_app.config["MAIL_USE_TLS"],
    )

    with SessionLocal() as session:
        service = AuthService(session, password_reset_mailer=mailer)

        service.request_password_reset(
            email=data["email"],
        )

        response = jsonify(
            {
                "message": (
                    "If an account exists for that email, "
                    "a password reset link has been sent."
                )
            }
        )

        return response, 200


@auth_bp.post("/reset-password")
def reset_password():
    data = cast(
        dict[str, Any],
        reset_password_schema.load(request.get_json()),
    )
    with SessionLocal() as session:
        service = AuthService(session)

        service.reset_password(
            raw_token=data["token"],
            new_password=data["new_password"],
        )

        response = jsonify({"message": "Password reset successfully."})

        return response, 200
