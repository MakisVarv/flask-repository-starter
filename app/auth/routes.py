# type: ignore
import uuid

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.auth.schema import login_schema, register_schema
from app.auth.service import AuthService
from app.config.database import SessionLocal
from app.users.schema import user_schema
from app.users.service import UserService

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth",
)


@auth_bp.post("/register")
def register():
    data = register_schema.load(request.get_json())

    with SessionLocal() as session:
        service = AuthService(session)

        user = service.register(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            password=data["password"],
            phone=data.get("phone"),
        )

        return user_schema.dump(user), 201


@auth_bp.post("/login")
def login():
    data = login_schema.load(request.get_json())

    with SessionLocal() as session:
        service = AuthService(session)

        user, access_token = service.login(
            email=data["email"],
            password=data["password"],
        )

        return {
            "access_token": access_token,
            "user": user_schema.dump(user),
        }, 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = uuid.UUID(get_jwt_identity())

    with SessionLocal() as session:
        service = UserService(session)
        user = service.get_user(user_id)

        return user_schema.dump(user), 200
