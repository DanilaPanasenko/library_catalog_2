import logging
from pathlib import Path
from datetime import datetime

# Директория для логов
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Формат записей
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOG_DIR / f"app_{datetime.now().strftime('%Y-%m-%d')}.log"


def setup_logger():
    """Настройка логгера"""
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE),  # Запись в файл
            logging.StreamHandler(),  # Вывод в консоль
        ]
    )
    # Пример логгера для конкретного модуля
    logger = logging.getLogger("book_catalog")
    logger.setLevel(logging.DEBUG)

    return logger


logger = setup_logger()
