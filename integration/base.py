import json
import httpx


from typing import Optional, Dict
from abc import ABC, abstractmethod


class BaseApiClient(ABC):
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.headers = self._get_default_headers()

    @abstractmethod
    def _get_default_headers(self) -> Dict[str, str]:
        """Должен возвращать заголовки по умолчанию для конкретного API"""
        pass

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict | None:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method,
                    url,
                    headers=self.headers,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, json.JSONDecodeError) as e:
            print(f"Request to {url} failed: {str(e)}")
            return None
