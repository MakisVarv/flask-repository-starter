from app.common.exceptions.base_exception import AppException


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized."):
        super().__init__(message, 401)
