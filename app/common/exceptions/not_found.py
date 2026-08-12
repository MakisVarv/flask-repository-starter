from app.common.exceptions.base_exception import AppException


class NotFoundException(AppException):

    def __init__(self, resource: str):

        super().__init__(
            f"{resource} not found.",
            404,
        )
