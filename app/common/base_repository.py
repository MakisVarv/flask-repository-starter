import uuid
from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.database import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, session: Session, model: type[ModelType]):
        self.session = session
        self.model = model

    def get_by_id(self, entity_id: uuid.UUID) -> ModelType | None:
        return self.session.get(self.model, entity_id)

    def get_all(self) -> Sequence[ModelType]:
        statement = select(self.model)
        return self.session.scalars(statement).all()

    def create(self, entity: ModelType) -> ModelType:
        self.session.add(entity)
        self.session.flush()
        self.session.refresh(entity)
        return entity

    def delete(self, entity: ModelType) -> None:
        self.session.delete(entity)
        self.session.flush()
