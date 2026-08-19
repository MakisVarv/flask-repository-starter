from flask_jwt_extended import JWTManager

from app.config.database import init_db

jwt = JWTManager()


@jwt.invalid_token_loader
def invalid_token_callback(reason):
    return {"message": "Invalid token."}, 401


def register_extensions(app):
    init_db(app)
    jwt.init_app(app)
