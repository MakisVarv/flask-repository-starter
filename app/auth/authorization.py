import uuid
from functools import wraps

from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.common.exceptions import ForbiddenException, UnauthorizedException
from app.config.database import SessionLocal


def has_permission(
    user,
    permission_name: str,
) -> bool:

    if user is None:
        return False

    if user.role is None:
        return False

    for permission in user.role.permissions:

        if permission.name == permission_name:
            return True

    return False


def permission_required(permission_name: str):
    def decorator(route_function):
        @wraps(route_function)
        def wrapper(*args, **kwargs):
            from app.users.service import UserService

            verify_jwt_in_request()
            user_id = uuid.UUID(get_jwt_identity())
            with SessionLocal() as session:
                service = UserService(session)
                user = service.get_user(user_id)
                if not user.is_active:
                    raise UnauthorizedException("Account is inactive.")
                allowed = has_permission(user, permission_name)
                if not allowed:
                    raise ForbiddenException(
                        "You do not have permission to perform this action."
                    )
            return route_function(*args, **kwargs)

        return wrapper

    return decorator
