from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageInfo(BaseModel):
    next_cursor: str | None = None
    limit: int = 50
    offset: int = 0
    next_offset: int | None = None
    has_next: bool = False


class ListResponse(BaseModel, Generic[T]):
    items: list[T]
    page_info: PageInfo = Field(default_factory=PageInfo)


class StatusResponse(BaseModel):
    status: str


def build_offset_page_info(*, item_count: int, limit: int, offset: int) -> PageInfo:
    has_next = item_count == limit
    return PageInfo(
        limit=limit,
        offset=offset,
        next_offset=offset + limit if has_next else None,
        has_next=has_next,
    )
