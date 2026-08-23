import uuid

from sqlalchemy.orm import Session

from app.auth.model import AuthSession


class AuthSessionRepository:

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, sid: uuid.UUID) -> AuthSession | None:
        return self.session.get(AuthSession, sid)

    def add(self, auth_session: AuthSession) -> None:
        self.session.add(auth_session)
