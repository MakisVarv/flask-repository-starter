import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from werkzeug.security import check_password_hash

from app.auth.model import AuthSession
from app.auth.password_reset.password_reset_exceptions import PasswordResetDeliveryError
from app.auth.password_reset.password_reset_model import PasswordResetToken
from app.auth.service import AuthService
from app.common.exceptions.bad_request import BadRequestException
from app.config.database import SessionLocal
from app.users.repository import UserRepository


class FakePasswordResetMailer:
    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    def send_password_reset(
        self,
        email: str,
        raw_token: str,
    ) -> None:
        self.sent.append(
            {
                "email": email,
                "raw_token": raw_token,
            }
        )


@pytest.fixture
def password_reset_mailer():
    return FakePasswordResetMailer()


def test_forgot_password_hides_email_delivery_failure(
    client,
    regular_user,
    monkeypatch,
):
    class FailingMailer:
        def send_password_reset(
            self,
            email: str,
            raw_token: str,
        ) -> None:
            raise PasswordResetDeliveryError("Failed to deliver password reset email.")

    monkeypatch.setattr(
        "app.auth.routes.SMTPPasswordResetMailer",
        lambda **kwargs: FailingMailer(),
    )

    response = client.post(
        "/api/auth/forgot-password",
        json={"email": regular_user["email"]},
    )

    assert response.status_code == 200
    assert (
        response.get_json()["message"] == "If an account exists for that email, "
        "a password reset link has been sent."
    )


def test_request_password_reset_creates_token_and_sends_email(
    regular_user,
    password_reset_mailer,
):
    with SessionLocal() as session:
        service = AuthService(
            session,
            password_reset_mailer=password_reset_mailer,
        )

        service.request_password_reset(regular_user["email"])

    assert len(password_reset_mailer.sent) == 1

    sent_email = password_reset_mailer.sent[0]

    assert sent_email["email"] == regular_user["email"]

    raw_token = sent_email["raw_token"]

    with SessionLocal() as session:
        reset_token = session.scalar(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == regular_user["id"]
            )
        )

        assert reset_token is not None

        expected_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        assert reset_token.token_hash == expected_hash
        assert reset_token.token_hash != raw_token
        assert reset_token.used_at is None
        assert reset_token.expires_at > datetime.now(timezone.utc)


def test_request_password_reset_unknown_email_sends_nothing(
    password_reset_mailer,
):
    with SessionLocal() as session:
        service = AuthService(
            session,
            password_reset_mailer=password_reset_mailer,
        )

        service.request_password_reset("unknown@example.com")

    assert password_reset_mailer.sent == []

    with SessionLocal() as session:
        reset_tokens = session.scalars(select(PasswordResetToken)).all()

        assert reset_tokens == []


def test_request_password_reset_inactive_user_sends_nothing(
    regular_user,
    password_reset_mailer,
):
    with SessionLocal() as session:
        user = UserRepository(session).get_by_id(regular_user["id"])

        assert user is not None

        user.is_active = False
        session.commit()

        service = AuthService(
            session,
            password_reset_mailer=password_reset_mailer,
        )

        service.request_password_reset(regular_user["email"])

    assert password_reset_mailer.sent == []


def test_new_password_reset_request_invalidates_previous_token(
    regular_user,
    password_reset_mailer,
):
    with SessionLocal() as session:
        service = AuthService(
            session,
            password_reset_mailer=password_reset_mailer,
        )

        service.request_password_reset(regular_user["email"])
        first_raw_token = password_reset_mailer.sent[-1]["raw_token"]

        service.request_password_reset(regular_user["email"])
        second_raw_token = password_reset_mailer.sent[-1]["raw_token"]

        assert first_raw_token != second_raw_token

        with pytest.raises(BadRequestException):
            service.reset_password(
                raw_token=first_raw_token,
                new_password="NewPassword123!",
            )


def test_reset_password_with_valid_token(
    regular_user,
    password_reset_mailer,
):
    new_password = "NewPassword123!"

    with SessionLocal() as session:
        service = AuthService(
            session,
            password_reset_mailer=password_reset_mailer,
        )

        service.request_password_reset(regular_user["email"])

        raw_token = password_reset_mailer.sent[0]["raw_token"]

        service.reset_password(
            raw_token=raw_token,
            new_password=new_password,
        )

    with SessionLocal() as session:
        user = UserRepository(session).get_by_id(regular_user["id"])

        assert user is not None
        assert check_password_hash(
            user.password_hash,
            new_password,
        )

        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        reset_token = session.scalar(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash
            )
        )

        assert reset_token is not None
        assert reset_token.used_at is not None


def test_used_password_reset_token_cannot_be_reused(
    regular_user,
    password_reset_mailer,
):
    with SessionLocal() as session:
        service = AuthService(
            session,
            password_reset_mailer=password_reset_mailer,
        )

        service.request_password_reset(regular_user["email"])

        raw_token = password_reset_mailer.sent[0]["raw_token"]

        service.reset_password(
            raw_token=raw_token,
            new_password="NewPassword123!",
        )

        with pytest.raises(BadRequestException):
            service.reset_password(
                raw_token=raw_token,
                new_password="AnotherPassword123!",
            )


def test_expired_password_reset_token_is_rejected(
    regular_user,
):
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    with SessionLocal() as session:
        expired_token = PasswordResetToken(
            user_id=regular_user["id"],
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )

        session.add(expired_token)
        session.commit()

        service = AuthService(session)

        with pytest.raises(BadRequestException):
            service.reset_password(
                raw_token=raw_token,
                new_password="NewPassword123!",
            )


def test_reset_password_revokes_existing_auth_sessions(
    client,
    regular_user,
    password_reset_mailer,
):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    assert login_response.status_code == 200

    with SessionLocal() as session:
        auth_session = session.scalar(
            select(AuthSession).where(AuthSession.user_id == regular_user["id"])
        )

        assert auth_session is not None
        assert auth_session.revoked_at is None

    with SessionLocal() as session:
        service = AuthService(
            session,
            password_reset_mailer=password_reset_mailer,
        )

        service.request_password_reset(regular_user["email"])

        raw_token = password_reset_mailer.sent[0]["raw_token"]

        service.reset_password(
            raw_token=raw_token,
            new_password="NewPassword123!",
        )

    with SessionLocal() as session:
        auth_session = session.scalar(
            select(AuthSession).where(AuthSession.user_id == regular_user["id"])
        )

        assert auth_session is not None
        assert auth_session.revoked_at is not None


def test_forgot_password_response_does_not_reveal_account_existence(
    client,
    regular_user,
    password_reset_mailer,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.auth.routes.SMTPPasswordResetMailer",
        lambda **kwargs: password_reset_mailer,
    )

    existing_response = client.post(
        "/api/auth/forgot-password",
        json={"email": regular_user["email"]},
    )

    unknown_response = client.post(
        "/api/auth/forgot-password",
        json={"email": "unknown@example.com"},
    )

    assert existing_response.status_code == 200
    assert unknown_response.status_code == 200

    assert existing_response.get_json() == unknown_response.get_json()

    assert (
        existing_response.get_json()["message"]
        == "If an account exists for that email, "
        "a password reset link has been sent."
    )

    assert len(password_reset_mailer.sent) == 1
