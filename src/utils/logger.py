import logging
from src.config.settings import LOG_DIR
from pathlib import Path

def setup_logging():
    """Настройка логирования"""
    log_file = LOG_DIR / "app.log"
    
    # Создаем директорию для логов, если она не существует
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Настраиваем формат логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Добавляем вывод в консоль
        ]
    )
    
    # Отключаем лишние логи от библиотек
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
