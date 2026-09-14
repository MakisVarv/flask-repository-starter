import uuid
from collections.abc import Sequence
from typing import Generic, TypeVar

from app.common.base_repository import BaseRepository
from app.common.exceptions.not_found import NotFoundException
from app.config.database import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseService(Generic[ModelType]):
    def __init__(
        self,
        repository: BaseRepository[ModelType],
        resource_name: str,
    ):
        self._base_repository = repository
        self.resource_name = resource_name

    def get_all(self) -> Sequence[ModelType]:
        return self._base_repository.get_all()

    def get_by_id(self, entity_id: uuid.UUID) -> ModelType:
        entity = self._base_repository.get_by_id(entity_id=entity_id)
        if entity is None:
            raise NotFoundException(self.resource_name)
        return entity
