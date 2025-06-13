from schemas.books import BookFilter
from schemas.storage_type import StorageType


class BookService:
    def __init__(self, adapter1, adapter2):
        self._adapter1 = adapter1
        self._adapter2 = adapter2

    def get_all_books(self, filters: BookFilter, storage_type: StorageType):
        if storage_type == StorageType.POSTGRES:
            books = self._adapter1.get_all_books(filters)
        if storage_type == StorageType.JSONBIN:
            books = self._adapter2.get_all_books(filters)
        return books
