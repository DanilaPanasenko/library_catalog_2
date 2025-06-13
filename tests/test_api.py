from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from fastapi import status


@pytest.mark.asyncio
async def test_create_book(mock_db, mock_adapters):
    test_book = {
        "title": "Harry Potter",
        "author": "Test Author",
        "year": 2023,
        "genre": "Fantasy",
        "pages": 1000,
        "cover_url": "https://example.com/cover.jpg",
        "description": "Test description",
        "availability": "available",
        "id": 1,
    }

    mock_adapters.return_value.create_book.return_value = test_book

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.post(
            "/add_books/",
            json={
                "title": "Harry Potter",
                "author": "Test Author",
                "year": 2023,
                "genre": "Fantasy",
                "pages": 1000,
                "availability": "available",
            },
            params={"storage": "postgres"},
        )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == test_book


@pytest.mark.asyncio
async def test_get_all_books(mock_db):
    # Настраиваем цепочку вызовов SQLAlchemy
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_limit = MagicMock()
    mock_offset = MagicMock()

    mock_db.return_value.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.limit.return_value = mock_limit
    mock_limit.offset.return_value = mock_offset

    # Создаем тестовую книгу
    mock_book = MagicMock()
    mock_book.id = 1
    mock_book.title = "Harry Potter"
    mock_book.author = "Test Author"
    mock_book.year = 2023
    mock_book.genre = "Fantasy"
    mock_book.pages = 1000
    mock_book.availability = "available"

    mock_offset.all.return_value = [mock_book]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.get(
            "/books/",
            params={
                "title": "Harry Potter",
                "limit": 10,
                "offset": 0,
                "storage_type": "postgres",
            },
        )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Harry Potter"


@pytest.mark.asyncio
async def test_get_book_by_id(mock_db):
    mock_book = {
        "title": "Harry Potter",
        "author": "Test Author",
        "year": 2023,
        "genre": "Fantasy",
        "pages": 1000,
        "cover_url": "https://covers.openlibrary.org/b/id/10523466-L.jpg",
        "description": "After the Dementors’ attack on his cousin Dudley, Harry knows he is about to become Voldemort’s next target.\r\n\r\nAlthough many are denying the Dark Lord’s return, Harry is not alone, and a secret order is gathering at Grimmauld Place to fight against the Dark forces.\r\n\r\nMeanwhile, Voldemort’s savage assaults on Harry’s mind are growing stronger every day.\r\n\r\nHe must allow Professor Snape to teach him to protect himself before he runs out of time.\r\n([source][1])\r\n\r\n\r\n----------\r\nThis work has also been published in multiple volumes. See:\r\n\r\n - [Harry Potter and the Order of the Phoenix: III](https://openlibrary.org/works/OL17937113W/Harry_Potter_and_the_Order_of_the_Phoenix_Chapters_17-23)\r\n - [Harry Potter and the Order of the Phoenix: IV](https://openlibrary.org/works/OL17915213W/Harry_Potter_and_the_Order_of_the_Phoenix_Chapters_24-30)\r\n\r\n  [1]: https://www.jkrowling.com/book/harry-potter-order-phoenix/",
        "availability": "available",
        "id": 1,
    }
    mock_db.get_book_by_id.return_value = mock_book

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.get(
            "/get_book/1", params={"book_id": 1, "storage_type": "postgres"}
        )
    assert response.status_code == 200
    assert response.json() == mock_book
