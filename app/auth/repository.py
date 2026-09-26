import uuid
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.auth.model import AuthSession


class AuthSessionRepository:

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, sid: uuid.UUID) -> AuthSession | None:
        return self.session.get(AuthSession, sid)

    def add(self, auth_session: AuthSession) -> None:
        self.session.add(auth_session)

    def revoke_all_for_user(
        self,
        user_id: uuid.UUID,
        revoked_at: datetime,
    ) -> None:
        stmt = (
            update(AuthSession)
            .where(
                AuthSession.user_id == user_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        self.session.execute(stmt)
