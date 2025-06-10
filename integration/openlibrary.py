import os


from typing import Optional, Dict, Any
from core.logger import logger
from integration.base import BaseApiClient
from dotenv import load_dotenv


class OpenLibraryClient(BaseApiClient):
    def __init__(self):
        super().__init__(base_url=os.getenv("OPENLIBRARY_URL"))
        self.covers_url = os.getenv("OPENLIBRARY_COVERS_URL")

    def _get_default_headers(self) -> Dict[str, str]:
        return {"Accept": "application/json"}

    async def search_books(self, title: str, limit: int = 1) -> Optional[Dict[str, Any]]:
        """Поиск книг по названию с получением обложки и описания"""
        try:
            # Шаг 1: Поиск книг
            search_data = await self._request(
                "GET",
                "search.json",
                params={"q": f"title:{title}", "limit": limit}
            )

            if not search_data or not search_data.get("docs"):
                return None

            book = search_data["docs"][0]  # Берем первую найденную книгу

            # Шаг 2: Получаем обложку
            cover_id = book.get("cover_i")
            cover_url = f"{self.covers_url}/id/{cover_id}-L.jpg" if cover_id else None

            # Шаг 3: Получаем описание (через work key)
            description = None
            if "key" in book:
                work_key = book["key"].replace("/works/", "")
                work_data = await self._request("GET", f"works/{work_key}.json")

                if work_data:
                    description = self._extract_description(work_data)

            return {
                "title": book.get("title"),
                "author": ", ".join(book.get("author_name", [])),
                "first_publish_year": book.get("first_publish_year"),
                "cover_url": cover_url,
                "description": description,
                "edition_key": book.get("edition_key", [""])[0],
                "work_key": work_key if "work_key" in locals() else None
            }

        except Exception as e:
            logger.error(f"Ошибка OpenLibrary API: {str(e)}")
            print(f"Ошибка OpenLibrary API: {str(e)}")
            return None

    def _extract_description(self, work_data: Dict) -> Optional[str]:
        """Извлекает описание из данных работы"""
        description = work_data.get("description")
        if isinstance(description, dict):
            return description.get("value")
        return description
