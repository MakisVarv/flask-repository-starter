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
