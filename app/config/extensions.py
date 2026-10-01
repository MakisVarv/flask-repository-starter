from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.config.database import init_db

cors = CORS()
jwt = JWTManager()

limiter = Limiter(
    key_func=get_remote_address,
)


@jwt.invalid_token_loader
def invalid_token_callback(reason: str):
    return {"message": "Invalid token."}, 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header: dict, jwt_payload: dict):
    token_type = jwt_payload.get("type")

    if token_type == "refresh":
        return {
            "message": "Refresh token expired.",
            "code": "refresh_token_expired",
        }, 401

    return {
        "message": "Access token expired.",
        "code": "access_token_expired",
    }, 401


def register_extensions(app: Flask) -> None:
    init_db(app)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": app.config["FRONTEND_ORIGIN"],
            }
        },
        supports_credentials=True,
    )
    limiter.init_app(app)
