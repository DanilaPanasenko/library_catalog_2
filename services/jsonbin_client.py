import os
from typing import Optional, Dict
from dotenv import load_dotenv

from services.base import BaseApiClient

load_dotenv()


class JsonBinClient(BaseApiClient):
    def __init__(self):
        super().__init__(base_url="https://api.jsonbin.io/v3")

    def _get_default_headers(self) -> Dict[str, str]:
        return {
            "X-Master-Key": os.getenv("JSONBIN_API_KEY"),
            "Content-Type": "application/json"
        }

    async def get_data(self, bin_id: str) -> Optional[Dict]:
        return await self._request("GET", f"b/{bin_id}")

    async def update_data(self, bin_id: str, data: Dict) -> bool:
        response = await self._request("PUT", f"b/{bin_id}", json=data)
        return response is not None

    async def create_bin(self, initial_data: Dict) -> Optional[str]:
        response = await self._request("POST", "b", json=initial_data)
        return response.get("metadata", {}).get("id") if response else None
