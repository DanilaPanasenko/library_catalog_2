from enum import Enum
from pydantic import BaseModel, HttpUrl


class AvailabilityStatus(str, Enum):
    """Для определения availability"""

    AVAILABLE = "available"
    BORROWED = "borrowed"


class BookBase(BaseModel):
    """Базовая pydentic схема для книг"""

    title: str
    author: str
    year: int
    genre: str
    pages: int
    cover_url: HttpUrl | None = None
    description: str | None = None
    availability: AvailabilityStatus = AvailabilityStatus.AVAILABLE


class BookCreate(BookBase):
    """pydentic схема для создания книг"""

    class Config:
        extra = "forbid"


class BookUpdate(BaseModel):
    """pydentic схема для изменения книг"""

    title: str | None
    author: str | None
    year: int | None
    genre: str | None
    pages: int | None
    availability: AvailabilityStatus | None = None


class Book(BookBase):
    """Полная pydentic схема с ID книги"""

    id: int
    # Дополнительные поля с информацией из Open Library API
    description: str | None = None
    cover_url: HttpUrl | None = None

    class Config:
        from_attributes = True


class BookFilter(BaseModel):
    title: str | None
    author: str | None
    genre: str | None = None
    limit: int | None = None
    offset: int | None = None
