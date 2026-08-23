from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from app.config.database import init_db

cors = CORS()
jwt = JWTManager()


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
