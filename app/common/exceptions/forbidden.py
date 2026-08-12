from app.common.exceptions.base_exception import AppException


class ForbiddenException(AppException):

    def __init__(self, message="Permission denied."):

        super().__init__(
            message,
            403,
        )
