from flask_jwt_extended import JWTManager

from app.config.database import init_db

jwt = JWTManager()


def register_extensions(app):
    init_db(app)
    jwt.init_app(app)
