import os
from typing import Optional

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from db.db import AsyncSessionLocal
from interfaces.books import JsonBinAdapter, StorageAdapter, PostgresAdapter
from schemas.books import BookFilter
from schemas.storage_type import StorageType
from integration.jsonbin_client import JsonBinClient
from integration.openlibrary import OpenLibraryClient
from dotenv import load_dotenv

from services.books import BookService

load_dotenv()


async def get_db() -> AsyncSession:
    """Получаем текущуюю сессию"""
    async with AsyncSessionLocal() as session:
        yield session


async def get_storage_type(
    storage: StorageType = Query(StorageType.POSTGRES),
) -> StorageType:  # Возвращаем StorageType, а не str
    """Зависимости для выбора хранилища"""
    return storage  # Enum уже гарантирует, что значение валидно


def get_jsonbin_id() -> str:
    return os.getenv("JSONBIN_BIN_ID")


def get_jsonbin_client() -> JsonBinClient:
    return JsonBinClient()


async def get_or_create_bin_id(
    bin_id=Depends(get_jsonbin_id), client=Depends(get_jsonbin_client)
) -> str:
    """Получает или создает новый bin"""
    bin_id = bin_id
    client = client
    try:
        await client.get_data(bin_id)
    except Exception as e:
        logger.info(f"Нет bin_id: {str(e)}")
        new_bin_id = await client.create_bin([])
        if new_bin_id:
            bin_id = new_bin_id
    return bin_id


def get_openlibrary_client() -> OpenLibraryClient:
    """Зависимость для получения объекта OpenLibrary"""
    return OpenLibraryClient()


def get_jsonbin_adapter(
    jsonbin_client: JsonBinClient = Depends(get_jsonbin_client),
    bin_id: str = Depends(get_or_create_bin_id),
    openlibrary_client: OpenLibraryClient = Depends(get_openlibrary_client),
):
    return JsonBinAdapter(jsonbin_client, bin_id, openlibrary_client)


def get_postgres_adapter(
    session: AsyncSessionLocal = Depends(get_db),
    openlibrary_client: OpenLibraryClient = Depends(get_openlibrary_client),
):
    return PostgresAdapter(session, openlibrary_client)


def get_storage_adapter(
    storage_type: StorageType,
    session: Optional[AsyncSessionLocal] = None,
    jsonbin_client: Optional[JsonBinClient] = None,
    bin_id: Optional[str] = None,
    openlibrary_client: Optional[OpenLibraryClient] = None,
    client=Depends(get_jsonbin_client),
    jsonbin_id=Depends(get_jsonbin_id),
) -> StorageAdapter:
    if storage_type == StorageType.POSTGRES:
        if not session:
            raise ValueError("Session is required for Postgres adapter")
        return PostgresAdapter(session, openlibrary_client)

    elif storage_type == StorageType.JSONBIN:
        if not jsonbin_client:
            jsonbin_client = client
        if not bin_id:
            bin_id = jsonbin_id
        return JsonBinAdapter(jsonbin_client, bin_id, openlibrary_client)

    raise ValueError(f"Unknown storage type: {storage_type}")


async def get_book_filter(
    title: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    offset: Optional[int] = Query(None),
) -> BookFilter:
    """Зависимость для получения фильтра книг"""
    return BookFilter(
        title=title, author=author, genre=genre, limit=limit, offset=offset
    )


def get_book_service(
    storage_type: StorageType = Query(StorageType.POSTGRES),
    adapter1=Depends(get_postgres_adapter),
    adapter2=Depends(get_jsonbin_adapter),
):
    return BookService(adapter1, adapter2)
