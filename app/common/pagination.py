from dataclasses import asdict, dataclass


@dataclass
class Pagination:
    page: int
    page_size: int
    total: int

    @property
    def offset(self) -> int:
        return self.page_size * (self.page - 1)

    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1

    def to_dict(self) -> dict[str, int | bool]:
        return {
            **asdict(self),
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_previous": self.has_previous,
        }
