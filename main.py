from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status, Query, Request
from fastapi.responses import JSONResponse
from core.exceptions import BookNotFoundError
from core.logger import logger
from db.db import engine, Base, get_db, AsyncSessionLocal
from dependencies.books import get_or_create_bin_id, get_openlibrary_client, get_storage_type, get_jsonbin_client, \
    get_storage_adapter, get_jsonbin_id, get_book_service
from schemas.books import BookCreate, BookFilter, BookUpdate, Book
from schemas.storage_type import StorageType
from integration.jsonbin_client import JsonBinClient
from integration.openlibrary import OpenLibraryClient
from services.books import BookService

app = FastAPI()


@app.exception_handler(BookNotFoundError)
async def book_not_found_handler(request: Request, exc: BookNotFoundError):
    logger.warning(f"Книга не найдена: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    logger.critical(f"Необработанная ошибка: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


@app.on_event("startup")
async def startup_event():
    """Функция для очистки и создания БД, использовать только во время разработки"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Удаляем старую
        await conn.run_sync(Base.metadata.create_all)  # Создаем новую


@app.post("/add_books/", status_code=status.HTTP_201_CREATED, tags=["Книги"], response_model=Book)
async def create_book(
    book_data: BookCreate,
    storage: StorageType = Query(StorageType.POSTGRES),
    session=Depends(get_db),
    jsonbin_client: JsonBinClient = Depends(get_jsonbin_client),
    bin_id: str = Depends(get_or_create_bin_id),
    openlibrary: OpenLibraryClient = Depends(get_openlibrary_client)
):
    """Эндпоинт для добавления новой книги"""
    adapter = get_storage_adapter(
        storage_type=storage,
        session=session,
        jsonbin_client=jsonbin_client,
        bin_id=bin_id,
        openlibrary_client=openlibrary
    )
    try:
        logger.info(f"Создания книги: '{book_data.title}' | Хранилище: {storage.value}")
        new_book = await adapter.create_book(book_data)
        logger.info(f"Книга создана: {new_book}")
        return new_book
    except Exception as e:
        logger.error(f"Ошибка создания книги: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания книги: {str(e)}"
        )


@app.get("/books/", tags=["Книги"], response_model=list[Book])
async def get_all_books(
    title: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    limit: Optional[int] = Query(10, ge=1, le=100),
    offset: Optional[int] = Query(0, ge=0),
    storage_type: StorageType = Query(StorageType.POSTGRES, description="Тип хранилища"),
    book_service: BookService = Depends(get_book_service),
):
    """Получение списка книг с фильтрацией"""
    book_filter = BookFilter(
        title=title,
        author=author,
        genre=genre,
        limit=limit,
        offset=offset,
        storage_type=storage_type
    )
    try:
        logger.info(f"Фильтрация {book_filter}")
        books = await book_service.get_all_books(book_filter, storage_type)
        logger.info(f"Получаем отфильтрованный список книг{books}")
        return books
    except Exception as e:
        logger.error(f"Ошибка получения книг: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения книг: {str(e)}"
        )


@app.get("/get_book/{book_id}", tags=["Книги"], response_model=Book)
async def get_book_by_id(
        book_id: int,
        storage_type: StorageType = Query(StorageType.POSTGRES, description="Тип хранилища"),
        session: AsyncSessionLocal = Depends(get_db),
        jsonbin_client: JsonBinClient = Depends(get_jsonbin_client),
        jsonbin_id: str = Depends(get_jsonbin_id),
):
    """Получить книгу по ID"""
    adapter = get_storage_adapter(
        storage_type=storage_type,
        session=session,
        jsonbin_client=jsonbin_client,
        bin_id=jsonbin_id,
    )

    try:
        logger.info(f"Поиск книги по ID: {book_id}")
        book = await adapter.get_book(book_id)
        logger.info(f"Получаем книгу по ID: {book}")
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Книга не найдена"
            )

        return book
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения книги: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения книги: {str(e)}"
        )


@app.put("/update_book/{book_id}", tags=["Книги"], response_model=Book)
async def update_book(
    book_id: int,
    book_data: BookUpdate,
    storage_type: StorageType = Depends(get_storage_type),
    session=Depends(get_db),
    jsonbin_client=Depends(get_jsonbin_client),
    jsonbin_id: str = Depends(get_jsonbin_id),
):
    """Обновление данных книги"""
    try:
        logger.info(f"Получаем книгу с ID: {book_id}")
        adapter = get_storage_adapter(storage_type, session, jsonbin_client, jsonbin_id)
        updated_book = await adapter.update_book(book_id, book_data)
    except Exception as e:
        logger.error(f"Книга не найдена: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена"
        )
    logger.info(f"Возвращаем книгу с обнавлением {updated_book}")
    return updated_book


@app.delete("/delete_book/{book_id}", tags=["Книги"])
async def delete_book(
    book_id: int,
    storage_type: StorageType = Depends(get_storage_type),
    session=Depends(get_db),
    jsonbin_client=Depends(get_jsonbin_client),
    jsonbin_id: str = Depends(get_jsonbin_id)
):
    """Удаление книги"""
    adapter = get_storage_adapter(storage_type, session, jsonbin_client, jsonbin_id)
    success = await adapter.delete_book(book_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена"
        )
    return {"message": "Книга успешно удалена"}
