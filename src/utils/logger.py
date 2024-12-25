import logging
from src.config.settings import LOG_FILE

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.DEBUG,  # Временно устанавливаем DEBUG
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
