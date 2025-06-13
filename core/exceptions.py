from fastapi import HTTPException, status


class BookNotFoundError(HTTPException):
    def __init__(self, book_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена",
        )


class ExternalApiError(HTTPException):
    def __init__(self, api_name: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Сервис {api_name} недоступен",
        )
