from sqlalchemy.orm import Mapped, mapped_column

from db.db import Base


class BookRepository(Base):
    """Главная модель для работы с БД"""
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str]
    author: Mapped[str]
    year: Mapped[int]
    genre: Mapped[str]
    pages: Mapped[int]
    availability: Mapped[bool] = True
    cover_url: Mapped[str | None]
    description: Mapped[str | None]
