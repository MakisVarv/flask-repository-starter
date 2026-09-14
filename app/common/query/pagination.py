from collections.abc import Sequence
from typing import TypeVar

from sqlalchemy import Select
from sqlalchemy.orm import Session

from app.config.database import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class Pagination:
    @staticmethod
    def paginate(
        *,
        session: Session,
        statement: Select[tuple[ModelType]],
        count_statement: Select[tuple[int]],
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[ModelType], dict[str, int | bool]]:
        page = max(page, 1)
        page_size = max(min(page_size, 100), 1)

        total = session.scalar(count_statement) or 0

        offset = (page - 1) * page_size

        items = session.scalars(statement.offset(offset).limit(page_size)).all()

        total_pages = (total + page_size - 1) // page_size

        return items, {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
        }
