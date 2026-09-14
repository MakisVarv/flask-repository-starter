from dataclasses import dataclass


@dataclass
class QueryOptions:
    page: int = 1
    page_size: int = 20
    sort_field: str = "id"
    descending: bool = False
