from flask import jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

from app.common.exceptions.base_exception import AppException


def register_error_handlers(app):

    @app.errorhandler(AppException)
    def handle_app_exception(error):

        return (
            jsonify(
                {
                    "message": error.message,
                }
            ),
            error.status_code,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):

        return (
            jsonify({"message": error.name}),
            error.code,
        )

    @app.errorhandler(ValidationError)
    def handle_validation(error):
        return (
            jsonify(
                {
                    "message": "Validation failed.",
                    "errors": error.messages,
                }
            ),
            400,
        )

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.exception("Unhandled exception", exc_info=error)

        return (
            jsonify({"message": "Internal server error."}),
            500,
        )
