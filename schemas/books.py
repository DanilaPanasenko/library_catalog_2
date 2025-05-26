from enum import Enum
from fastapi import Query
from pydantic import BaseModel, HttpUrl
from typing import Optional


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
    cover_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    availability: AvailabilityStatus = AvailabilityStatus.AVAILABLE


class BookCreate(BookBase):
    """pydentic схема для создания книг"""
    class Config:
        extra = "forbid"


class BookUpdate(BaseModel):
    """pydentic схема для изменения книг"""
    title: Optional[str]
    author: Optional[str]
    year: Optional[int]
    genre: Optional[str]
    pages: Optional[int]
    availability: Optional[AvailabilityStatus] = None


class Book(BookBase):
    """Полная pydentic схема с ID книги"""
    id: int
    # Дополнительные поля с информацией из Open Library API
    description: Optional[str] = None
    cover_url: Optional[HttpUrl] = None

    class Config:
        from_attributes = True


class BookFilter(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


async def get_book_filter(
    title: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    offset: Optional[int] = Query(None)
) -> BookFilter:
    """Зависимость для получения фильтра книг"""
    return BookFilter(
        title=title,
        author=author,
        genre=genre,
        limit=limit,
        offset=offset
    )
