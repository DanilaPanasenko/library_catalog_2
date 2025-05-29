from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from db.db import Base


class BookModel(Base):
    """Главная модель для работы с БД"""
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(comment="Наименование книги")
    author: Mapped[str] = mapped_column(comment="Имя автора")
    year: Mapped[int] = mapped_column(comment="Год издания книги")
    genre: Mapped[str] = mapped_column(comment="Жанр книги")
    pages: Mapped[int] = mapped_column(comment="Количество страниц книги")
    availability: Mapped[str] = mapped_column(String(20), default="available", comment="Статус доступности")
    cover_url: Mapped[str | None] = mapped_column(comment="Ссылка на обложку")
    description: Mapped[str | None] = mapped_column(comment="Описание книги")
