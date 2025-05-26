from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import AsyncSessionLocal
from interfaces.books import get_jsonbin_id, get_jsonbin_client, JsonBinAdapter
from schemas.storage_type import StorageType
from services.jsonbin_client import JsonBinClient


async def get_db() -> AsyncSession:
    """Получаем текущуюю сессию"""
    async with AsyncSessionLocal() as session:
        yield session


async def get_storage_type(
    storage: StorageType = Query(StorageType.POSTGRES)
) -> StorageType:  # Возвращаем StorageType, а не str
    return storage  # Enum уже гарантирует, что значение валидно


async def get_or_create_bin_id() -> str:
    """Получает или создает новый bin"""
    bin_id = get_jsonbin_id()
    client = get_jsonbin_client()
    try:
        await client.get_data(bin_id)
    except:
        new_bin_id = await client.create_bin([])
        if new_bin_id:
            bin_id = new_bin_id
    return bin_id


async def get_jsonbin_adapter(
    client: JsonBinClient = Depends(get_jsonbin_client),
    bin_id: str = Depends(get_or_create_bin_id)
) -> JsonBinAdapter:
    return JsonBinAdapter(client, bin_id)
