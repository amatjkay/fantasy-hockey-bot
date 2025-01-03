import os
import logging
from datetime import datetime
from pathlib import Path
from .settings import LOGS_DIR

def setup_logging(name: str) -> logging.Logger:
    """
    Настройка логгера для компонента
    
    Args:
        name: Имя компонента (app, api, scripts)
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    # Создаем директорию для логов текущего месяца
    current_month = datetime.now().strftime('%Y-%m')
    log_dir = LOGS_DIR / name / current_month
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Пути к файлам логов
    log_file = log_dir / f'{name}.log'
    error_file = log_dir / 'error.log'
    
    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Форматтер для логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Обработчик для всех логов
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Обработчик для ошибок
    error_handler = logging.FileHandler(error_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Добавляем обработчики к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger

def cleanup_old_logs(months_to_keep: int = 3) -> None:
    """
    Удаление старых логов
    
    Args:
        months_to_keep: Количество месяцев, за которые сохранять логи
    """
    # TODO: Реализовать очистку старых логов
    pass 