import logging
import os
from pathlib import Path

def setup_logging(name: str = None) -> logging.Logger:
    """Настройка логирования
    
    Args:
        name (str, optional): Имя логгера. По умолчанию None.
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    # Создаем директорию для логов если её нет
    log_dir = Path(__file__).parent.parent / 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Настраиваем формат
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Хендлер для файла
    file_handler = logging.FileHandler(
        os.path.join(log_dir, 'app.log'),
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Хендлер для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Получаем логгер
    logger = logging.getLogger(name if name else __name__)
    logger.setLevel(logging.INFO)
    
    # Добавляем хендлеры
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger 