import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth.password_reset.password_reset_model import PasswordResetToken
from app.common.base_repository import BaseRepository


class PasswordResetTokenRepository(BaseRepository[PasswordResetToken]):

    def __init__(self, session: Session) -> None:
        super().__init__(session, PasswordResetToken)

    def get_valid_by_hash(
        self,
        token_hash: str,
        now: datetime,
    ) -> PasswordResetToken | None:
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def delete_unused_for_user(
        self,
        user_id: uuid.UUID,
    ) -> None:
        stmt = delete(PasswordResetToken).where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
        )

        self.session.execute(stmt)
