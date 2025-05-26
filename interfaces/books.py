import os
import httpx


from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from sqlalchemy import select, and_
from db.db import AsyncSessionLocal
from models.books import BookRepository
from schemas.books import BookFilter, BookCreate, BookUpdate
from schemas.storage_type import StorageType
from services.jsonbin_client import JsonBinClient
from services.openlibrary import OpenLibraryClient
from dotenv import load_dotenv


load_dotenv()


class StorageAdapter(ABC):
    """Создаем абстрактный интерфейс для работы с хранилещами"""

    @abstractmethod
    async def get_all_books(self, book_filter: BookFilter) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_book(self, book_id: int) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def create_book(self, book_data: BookCreate) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def update_book(self, book_id: int, book_data: BookUpdate) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def delete_book(self, book_id: int) -> bool:
        pass


class PostgresAdapter(StorageAdapter):
    """Создаем адаптер для Postgres"""
    def __init__(self, session: AsyncSessionLocal, openlibrary_client: Optional[OpenLibraryClient] = None):
        self.session = session
        self.openlibrary = openlibrary_client

    async def create_book(self, book_data: BookCreate) -> Dict[str, Any]:
        """Получаем данные из OpenLibrary по названию (если нужно)"""
        extra_data = {}
        if self.openlibrary and book_data.title:
            ol_data = await self.openlibrary.search_books(book_data.title)
            if ol_data:
                extra_data = {
                    "cover_url": ol_data.get("cover_url"),
                    "description": ol_data.get("description"),
                }
                # Добавляем автора и год ТОЛЬКО если они не указаны в запросе
                if not book_data.author and ol_data.get("author"):
                    extra_data["author"] = ol_data["author"]
                if not book_data.year and ol_data.get("first_publish_year"):
                    extra_data["year"] = ol_data["first_publish_year"]

        # Создаем книгу, объединяя данные
        db_book = BookRepository(
            **book_data.model_dump(exclude_unset=True),  # Основные данные из запроса
            **extra_data  # Доп. данные из OpenLibrary
        )
        self.session.add(db_book)
        await self.session.commit()
        await self.session.refresh(db_book)
        return db_book

    async def get_all_books(self, book_filter: BookFilter) -> List[Dict[str, Any]]:
        """Получаем книги по фильтрам либо все"""
        query = select(BookRepository)

        filters = []
        if book_filter.title:
            filters.append(BookRepository.title == book_filter.title)
        if book_filter.author:
            filters.append(BookRepository.author == book_filter.author)
        if book_filter.genre:
            filters.append(BookRepository.genre == book_filter.genre)
        # Проверяем есть ли условаия
        if filters:
            query = query.where(and_(*filters))
        # Пагинация
        if book_filter.limit:
            query = query.limit(book_filter.limit)
        if book_filter.offset:
            query = query.offset(book_filter.offset)

        result = await self.session.execute(query)
        # Преобразует результат в объекты python и извлекает все строки
        return result.scalars().all()

    async def get_book(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Получаем книгу по ID"""
        result = await self.session.execute(select(BookRepository).where(BookRepository.id == book_id))
        book = result.scalars().first()
        return book

    async def update_book(self, book_id: int, book_data: BookUpdate) -> Optional[Dict[str, Any]]:
        """Обнавляем данные о книги"""
        result = await self.session.execute(select(BookRepository).where(BookRepository.id == book_id))
        db_book = result.scalars().first()
        if not db_book:
            return None

        update_data = book_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_book, key, value)

        await self.session.commit()
        await self.session.refresh(db_book)
        return db_book

    async def delete_book(self, book_id: int) -> bool:
        """Удааяем книгу из бд"""
        result = await self.session.execute(select(BookRepository).where(BookRepository.id == book_id))
        db_book = result.scalars().first()
        if not db_book:
            return False

        await self.session.delete(db_book)
        await self.session.commit()
        return True


class JsonBinAdapter(StorageAdapter):
    """Создаем адаптер для JsonBin"""

    def __init__(self, client: JsonBinClient, bin_id: str, openlibrary_client: Optional[OpenLibraryClient] = None):
        self.client = client
        self.bin_id = bin_id
        self.openlibrary = openlibrary_client

    async def _get_all_data(self) -> List[Dict[str, Any]]:
        """Получает текущий список книг из хранилища"""
        headers = {
            "X-Master-Key": os.getenv("JSONBIN_API_KEY")
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.jsonbin.io/v3/b/{self.bin_id}",
                    headers=headers
                )
                data = response.json()
                # Извлекаем массив книг из объекта
                return data.get("record", {}).get("books", [])
        except Exception as e:
            print(f"Ошибка получения данных: {str(e)}")
            return []

    async def _update_data(self, data: List[Dict[str, Any]]) -> bool:
        headers = {
            "Content-Type": "application/json",
            "X-Master-Key": os.getenv("JSONBIN_API_KEY"),
            "X-Bin-Versioning": "false"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"https://api.jsonbin.io/v3/b/{self.bin_id}",
                    json={"books": data},  # Убедитесь, что структура соответствует ожиданиям
                    headers=headers
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Ошибка при обновлении bin: {str(e)}")
            return False

    async def get_all_books(self, book_filter: BookFilter) -> List[Dict[str, Any]]:
        """Получить все книги с фильтрацией"""
        books = await self._get_all_data()

        # Применяем фильтрацию
        if book_filter.title:
            books = [b for b in books if b.get('title') == book_filter.title]
        if book_filter.author:
            books = [b for b in books if b.get('author') == book_filter.author]
        if book_filter.genre:
            books = [b for b in books if b.get('genre') == book_filter.genre]

        # Применяем пагинацию
        if book_filter.offset:
            books = books[book_filter.offset:]
        if book_filter.limit:
            books = books[:book_filter.limit]

        return books

    async def get_book(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Получить книгу по ID"""
        books = await self._get_all_data()
        for book in books:
            if isinstance(book, dict) and book.get('id') == book_id:
                return book
        return None

    async def create_book(self, book_data: BookCreate) -> Dict[str, Any]:
        await self._ensure_bin_exists()

        # Получаем данные из OpenLibrary по названию
        extra_data = {}
        if self.openlibrary and book_data.title:
            ol_data = await self.openlibrary.search_books(book_data.title)
            if ol_data:
                extra_data = {
                    "cover_url": ol_data.get("cover_url"),
                    "description": ol_data.get("description"),
                    "author": ol_data.get("author", book_data.author),
                    "year": ol_data.get("first_publish_year", book_data.year)
                }

        books = await self._get_all_data()
        new_id = max([b.get("id", 0) for b in books], default=0) + 1

        new_book = {
            "id": new_id,
            **book_data.model_dump(exclude_unset=True),
            **extra_data
        }

        books.append(new_book)
        success = await self._update_data(books)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Не удалось сохранить книгу в JSONBin"
            )
        return new_book

    async def _ensure_bin_exists(self):
        """Проверяет существование bin"""
        try:
            await self.client.get_data(self.bin_id)
        except:
            await self.client.create_bin({"books": []})

    async def update_book(
            self,
            book_id: int,
            book_data: BookUpdate
    ) -> Optional[Dict[str, Any]]:
        """Обновить данные книги"""
        books = await self._get_all_data()
        updated_book = None

        for book in books:
            if isinstance(book, dict) and book.get('id') == book_id:
                book.update(book_data.model_dump(exclude_unset=True))
                updated_book = book
                break

        if updated_book and await self._update_data(books):
            return updated_book
        return None

    async def delete_book(self, book_id: int) -> bool:
        """Удалить книгу"""
        books = await self._get_all_data()
        initial_length = len(books)
        books = [b for b in books if isinstance(b, dict) and b.get('id') != book_id]

        if len(books) < initial_length:
            return await self._update_data(books)
        return False


def get_jsonbin_client() -> JsonBinClient:
    return JsonBinClient()


def get_jsonbin_id() -> str:
    return os.getenv("JSONBIN_BIN_ID")


def get_storage_adapter(
        storage_type: StorageType,
        session: Optional[AsyncSessionLocal] = None,
        jsonbin_client: Optional[JsonBinClient] = None,
        bin_id: Optional[str] = None,
        openlibrary_client: Optional[OpenLibraryClient] = None
) -> StorageAdapter:
    if storage_type == StorageType.POSTGRES:
        if not session:
            raise ValueError("Session is required for Postgres adapter")
        return PostgresAdapter(session, openlibrary_client)

    elif storage_type == StorageType.JSONBIN:
        if not jsonbin_client:
            jsonbin_client = get_jsonbin_client()
        if not bin_id:
            bin_id = get_jsonbin_id()
        return JsonBinAdapter(jsonbin_client, bin_id, openlibrary_client)

    raise ValueError(f"Unknown storage type: {storage_type}")
