import uuid
from datetime import datetime, timezone
from typing import Any

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash

from app.auth.model import AuthSession
from app.auth.repository import AuthSessionRepository
from app.common.exceptions import NotFoundException, UnauthorizedException
from app.users import UserRepository, UserService
from app.users.model import User


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.user_service = UserService(session)
        self.user_repository = UserRepository(session)
        self.auth_session_repository = AuthSessionRepository(session)

    def register(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        phone: str | None = None,
    ) -> User:
        return self.user_service.register_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            phone=phone,
        )

    def login(
        self,
        email: str,
        password: str,
    ) -> tuple[User, str, str]:

        user = self.user_repository.get_by_email(email)

        if user is None:
            raise UnauthorizedException("Invalid email or password.")

        password_ok = check_password_hash(user.password_hash, password)

        if not user.is_active:
            raise UnauthorizedException("Invalid email or password.")
        if not password_ok:
            raise UnauthorizedException("Invalid email or password.")

        sid = uuid.uuid4()

        access_token = create_access_token(
            identity=str(user.id),
            fresh=True,
            additional_claims={"sid": str(sid)},
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims={"sid": str(sid)},
        )
        refresh_payload = decode_token(refresh_token)
        refresh_jti = refresh_payload["jti"]

        refresh_expires_at = datetime.fromtimestamp(
            refresh_payload["exp"],
            tz=timezone.utc,
        )
        auth_session = AuthSession(
            id=sid,
            user_id=user.id,
            current_refresh_jti=refresh_jti,
            expires_at=refresh_expires_at,
        )
        self.auth_session_repository.add(auth_session)
        self.session.commit()
        return user, access_token, refresh_token

    def get_current_user(self, user_id: uuid.UUID) -> User:
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise NotFoundException("User")

        if not user.is_active:
            raise UnauthorizedException("Account is inactive.")

        return user

    def refresh(
        self,
        user_id: uuid.UUID,
        sid: uuid.UUID,
        refresh_jti: str,
    ) -> tuple[str, str]:
        auth_session = self.auth_session_repository.get_by_id(sid)

        if auth_session is None:
            raise UnauthorizedException("Invalid refresh session.")

        if auth_session.revoked_at is not None:
            raise UnauthorizedException("Refresh session revoked.")

        if auth_session.expires_at <= datetime.now(timezone.utc):
            raise UnauthorizedException("Refresh session expired.")

        if auth_session.current_refresh_jti != refresh_jti:
            auth_session.revoked_at = datetime.now(timezone.utc)
            self.session.commit()

            raise UnauthorizedException("Invalid refresh token.")

        if auth_session.user_id != user_id:
            raise UnauthorizedException("Invalid refresh session.")
        user = self.user_repository.get_by_id(user_id)

        if user is None or not user.is_active:
            raise UnauthorizedException("Invalid refresh session.")

        new_access_token = create_access_token(
            identity=str(user.id),
            fresh=False,
            additional_claims={"sid": str(sid)},
        )

        new_refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims={"sid": str(sid)},
        )

        new_refresh_payload = decode_token(new_refresh_token)

        auth_session.current_refresh_jti = new_refresh_payload["jti"]
        auth_session.expires_at = datetime.fromtimestamp(
            new_refresh_payload["exp"],
            tz=timezone.utc,
        )

        self.session.commit()

        return new_access_token, new_refresh_token

    def update_current_user(self, user_id: uuid.UUID, data: dict[str, Any]) -> User:
        user = self.get_current_user(user_id)
        if "first_name" in data:
            user.first_name = data["first_name"]

        if "last_name" in data:
            user.last_name = data["last_name"]

        if "phone" in data:
            user.phone = data["phone"]

        self.session.commit()

        return user

    def logout(
        self,
        user_id: uuid.UUID,
        sid: uuid.UUID,
        refresh_jti: str,
    ) -> None:

        auth_session = self.auth_session_repository.get_by_id(sid)

        if auth_session is None:
            raise UnauthorizedException("Invalid refresh session.")

        if auth_session.user_id != user_id:
            raise UnauthorizedException("Invalid refresh session.")

        if auth_session.current_refresh_jti != refresh_jti:
            raise UnauthorizedException("Invalid refresh token.")

        auth_session.revoked_at = datetime.now(timezone.utc)

        self.session.commit()
