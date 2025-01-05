import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime

def setup_logging(service_name: str = None) -> None:
    """
    Настраивает систему логирования с разделением по типам событий
    
    Args:
        service_name (str): Имя сервиса для создания отдельной директории логов
    """
    # Создаем базовую директорию для логов
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Если указано имя сервиса, создаем поддиректорию
    if service_name:
        current_month = datetime.now().strftime('%Y-%m')
        service_log_dir = log_dir / service_name / current_month
        service_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Настраиваем логи для сервиса
        setup_service_logging(service_name, service_log_dir)
    else:
        # Настраиваем общие логи
        setup_general_logging(log_dir)

def setup_service_logging(service_name: str, log_dir: Path) -> None:
    """
    Настраивает логирование для конкретного сервиса
    
    Args:
        service_name (str): Имя сервиса
        log_dir (Path): Директория для логов
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.DEBUG)
    
    # Форматтер для логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Обработчик для всех сообщений
    general_handler = RotatingFileHandler(
        log_dir / 'service.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    general_handler.setLevel(logging.INFO)
    general_handler.setFormatter(formatter)
    
    # Обработчик для ошибок
    error_handler = RotatingFileHandler(
        log_dir / 'error.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Обработчик для отладки
    debug_handler = RotatingFileHandler(
        log_dir / 'debug.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=3
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    
    # Добавляем обработчики к логгеру
    logger.addHandler(general_handler)
    logger.addHandler(error_handler)
    logger.addHandler(debug_handler)

def setup_general_logging(log_dir: Path) -> None:
    """
    Настраивает общее логирование
    
    Args:
        log_dir (Path): Директория для логов
    """
    # Форматтер для логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Обработчик для файла
    file_handler = RotatingFileHandler(
        log_dir / 'app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Возвращает настроенный логгер для компонента
    
    Args:
        name (str): Имя компонента
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    return logging.getLogger(name) 