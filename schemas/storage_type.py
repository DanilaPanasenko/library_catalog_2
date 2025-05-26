from enum import Enum
from pydantic import BaseModel, ConfigDict


class StorageType(str, Enum):
    """Выбираем способ хранения данных"""
    POSTGRES = "postgres"
    JSONBIN = "jsonbin"

    @classmethod
    def get_values(cls):
        return [member.value for member in cls]


# Обновленная модель с явным указанием конфигурации
class StorageTypeResponse(BaseModel):
    storage_type: StorageType

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "storage_type": "postgres"
            }
        }
    )
