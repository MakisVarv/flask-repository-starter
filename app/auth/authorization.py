from functools import wraps

from flask_jwt_extended import get_jwt_identity

from app.common.exceptions.forbidden import ForbiddenException
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

            user_id = get_jwt_identity()
            print("JWT:", user_id)
            with SessionLocal() as session:
                service = UserService(session)
                user = service.get_user(user_id)
                allowed = has_permission(user, permission_name)
                if not allowed:
                    raise ForbiddenException(
                        "You do not have permission to perform this action."
                    )

                print("Allowed:", True)

            return route_function(*args, **kwargs)

        return wrapper

    return decorator
