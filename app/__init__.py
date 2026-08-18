from flask import Flask

from app.auth.routes import auth_bp
from app.common.error_handler import register_error_handlers
from app.config.config import Config
from app.config.extensions import register_extensions
from app.permissions import permission_bp
from app.roles import role_bp
from app.users import user_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    register_extensions(app)
    register_error_handlers(app)
    app.register_blueprint(role_bp)
    app.register_blueprint(permission_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)

    return app
