from flask_jwt_extended import create_access_token
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash

from app.common.exceptions.base_exception import AppException
from app.common.exceptions.not_found import NotFoundException
from app.roles import RoleRepository
from app.users import UserRepository, UserService


class AuthService:
    def __init__(self, session: Session):
        self.session = session
        self.role_repository = RoleRepository(session)
        self.user_service = UserService(session)
        self.user_repository = UserRepository(session)

    def register(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        phone: str | None = None,
    ):
        user_role = self.role_repository.get_by_name("User")

        if user_role is None:
            raise NotFoundException("User role")

        return self.user_service.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            phone=phone,
            role_id=user_role.id,
        )

    def login(
        self,
        email: str,
        password: str,
    ):

        user = self.user_repository.get_by_email(email)

        if user is None:
            raise AppException("Invalid email or password.", 401)

        password_ok = check_password_hash(user.password_hash, password)

        if not user.is_active:
            raise AppException("Invalid email or password.", 401)
        if not password_ok:
            raise AppException("Invalid email or password.", 401)

        access_token = create_access_token(identity=str(user.id))

        return user, access_token
