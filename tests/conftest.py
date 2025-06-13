import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def mock_db(mocker):
    mock = MagicMock()
    print(f"\nCreating mock DB: {mock}")
    mocker.patch("main.get_db", return_value=mock)
    return mock


@pytest.fixture
def mock_adapters(mocker):
    mocker.patch("main.get_jsonbin_client", return_value=AsyncMock())
    mocker.patch("main.get_openlibrary_client", return_value=AsyncMock())
    return mocker.patch("main.get_storage_adapter", return_value=AsyncMock())
