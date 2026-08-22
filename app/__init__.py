from flask import Flask

from app.auth.routes import auth_bp
from app.common.error_handler import register_error_handlers
from app.config.config import Config
from app.config.extensions import register_extensions
from app.permissions import permission_bp
from app.roles import role_bp
from app.users import user_bp


def _validate_config(app: Flask) -> None:
    required = (
        "DATABASE_URL",
        "JWT_SECRET_KEY",
    )

    missing = [key for key in required if not app.config.get(key)]

    if missing:
        raise RuntimeError(f"Missing required configuration: {', '.join(missing)}")


def create_app(config_class: type[Config] = Config):
    app = Flask(__name__)

    app.config.from_object(config_class)
    _validate_config(app)

    register_extensions(app)
    register_error_handlers(app)

    app.register_blueprint(role_bp)
    app.register_blueprint(permission_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)

    return app
