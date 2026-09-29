import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from app.auth.model import AuthSession
from app.auth.password_reset.password_reset_mailer import PasswordResetMailer
from app.auth.password_reset.password_reset_model import PasswordResetToken
from app.auth.password_reset.password_reset_repository import (
    PasswordResetTokenRepository,
)
from app.auth.repository import AuthSessionRepository
from app.common.exceptions import NotFoundException, UnauthorizedException
from app.common.exceptions.bad_request import BadRequestException
from app.users.model import User
from app.users.repository import UserRepository
from app.users.service import UserService


class AuthService:

    def __init__(
        self,
        session: Session,
        password_reset_mailer: PasswordResetMailer | None = None,
    ) -> None:
        self.session = session
        self.user_service = UserService(session)
        self.user_repository = UserRepository(session)
        self.auth_session_repository = AuthSessionRepository(session)
        self.password_reset_repository = PasswordResetTokenRepository(session)
        self.password_reset_mailer = password_reset_mailer

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

    def change_password(
        self,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        user = self.get_current_user(user_id)

        password_ok = check_password_hash(user.password_hash, current_password)

        if not password_ok:
            raise UnauthorizedException("Invalid password.")
        try:
            user.password_hash = generate_password_hash(new_password)

            revoked_at = datetime.now(timezone.utc)

            self.auth_session_repository.revoke_all_for_user(
                user_id=user.id,
                revoked_at=revoked_at,
            )

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

    def change_email(
        self,
        user_id: uuid.UUID,
        current_password: str,
        new_email: str,
    ) -> None:
        user = self.get_current_user(user_id)

        password_ok = check_password_hash(user.password_hash, current_password)

        if not password_ok:
            raise UnauthorizedException("Invalid password.")

        existing_user = self.user_repository.get_by_email(new_email)

        if existing_user is not None and existing_user.id != user.id:
            raise BadRequestException("Email already exists.")
        if new_email == user.email:
            return
        try:
            user.email = new_email
            revoked_at = datetime.now(timezone.utc)

            self.auth_session_repository.revoke_all_for_user(
                user_id=user.id,
                revoked_at=revoked_at,
            )
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def logout_all(
        self,
        user_id: uuid.UUID,
    ) -> None:
        user = self.get_current_user(user_id)

        try:
            revoked_at = datetime.now(timezone.utc)

            self.auth_session_repository.revoke_all_for_user(
                user_id=user.id,
                revoked_at=revoked_at,
            )
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def request_password_reset(
        self,
        email: str,
    ) -> None:
        user = self.user_repository.get_by_email(email=email)
        if user is None or not user.is_active:
            return
        if self.password_reset_mailer is None:
            raise RuntimeError("Password reset mailer is not configured.")
        try:
            self.password_reset_repository.delete_unused_for_user(user_id=user.id)
            raw_token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(minutes=30)
            self.password_reset_repository.create(
                PasswordResetToken(
                    user_id=user.id, token_hash=token_hash, expires_at=expires_at
                )
            )
            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        self.password_reset_mailer.send_password_reset(
            email=user.email,
            raw_token=raw_token,
        )

    def reset_password(
        self,
        raw_token: str,
        new_password: str,
    ) -> None:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        now = datetime.now(timezone.utc)

        reset_token = self.password_reset_repository.get_valid_by_hash(
            token_hash=token_hash,
            now=now,
        )
        if reset_token is None:
            raise BadRequestException("Invalid or expired password reset token.")
        user = self.user_repository.get_by_id(reset_token.user_id)
        if user is None or not user.is_active:
            raise BadRequestException("Invalid or expired password reset token.")
        try:
            user.password_hash = generate_password_hash(new_password)
            reset_token.used_at = now
            self.session.flush()
            self.password_reset_repository.delete_unused_for_user(user_id=user.id)
            self.auth_session_repository.revoke_all_for_user(
                user_id=user.id, revoked_at=now
            )
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def reauthenticate(
        self,
        user_id: uuid.UUID,
        sid: uuid.UUID,
        current_password: str,
    ) -> str:
        user = self.get_current_user(user_id)
        auth_session = self.auth_session_repository.get_by_id(sid)
        if auth_session is None:
            raise UnauthorizedException("Invalid session.")

        if auth_session.revoked_at is not None:
            raise UnauthorizedException("Invalid session.")

        if auth_session.expires_at <= datetime.now(timezone.utc):
            raise UnauthorizedException("Invalid session.")

        if auth_session.user_id != user_id:
            raise UnauthorizedException("Invalid session.")

        password_ok = check_password_hash(user.password_hash, current_password)
        if not password_ok:
            raise UnauthorizedException("Invalid password.")
        access_token = create_access_token(
            identity=str(user.id),
            fresh=timedelta(minutes=10),
            additional_claims={"sid": str(sid)},
        )
        return access_token
