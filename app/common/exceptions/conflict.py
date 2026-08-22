from app.common.exceptions.base_exception import AppException


class ConflictException(AppException):
    def __init__(self, message: str = "Conflict."):
        super().__init__(message, 409)
