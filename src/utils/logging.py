import logging
import os
from typing import Optional

def setup_logging(name: str, level: Optional[int] = None) -> logging.Logger:
    """Настройка логирования
    
    Args:
        name (str): Имя логгера
        level (Optional[int]): Уровень логирования
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    # Создаем директорию для логов если не существует
    os.makedirs('logs', exist_ok=True)
    
    # Создаем логгер
    logger = logging.getLogger(name)
    
    # Устанавливаем уровень логирования
    if level is None:
        level = logging.INFO
    logger.setLevel(level)
    
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Добавляем обработчик для файла
    file_handler = logging.FileHandler(f'logs/{name}.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Добавляем обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger 