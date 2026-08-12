from app.common.exceptions.base_exception import AppException


class BadRequestException(AppException):

    def __init__(self, message):

        super().__init__(
            message,
            400,
        )
