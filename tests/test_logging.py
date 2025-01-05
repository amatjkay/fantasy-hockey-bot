import pytest
import logging
import os
from pathlib import Path
from datetime import datetime
import shutil
from src.config.logging_config import setup_logging, get_logger

@pytest.fixture
def cleanup_logs():
    """Очищает тестовые логи после каждого теста"""
    log_dir = Path('logs')
    if log_dir.exists():
        shutil.rmtree(log_dir)
    yield
    if log_dir.exists():
        shutil.rmtree(log_dir)

def test_setup_general_logging(cleanup_logs):
    """Тест настройки общего логирования"""
    # Настраиваем логирование
    setup_logging()
    
    # Получаем тестовый логгер
    logger = get_logger('test_general')
    
    # Проверяем создание директории
    log_dir = Path('logs')
    assert log_dir.exists()
    
    # Проверяем создание файла логов
    log_file = log_dir / 'app.log'
    assert log_file.exists()
    
    # Пишем тестовые сообщения
    test_message = "Test general logging message"
    logger.info(test_message)
    
    # Проверяем запись в файл
    with open(log_file, 'r') as f:
        content = f.read()
        assert test_message in content

def test_setup_service_logging(cleanup_logs):
    """Тест настройки логирования для сервиса"""
    service_name = 'test_service'
    
    # Настраиваем логирование
    setup_logging(service_name)
    
    # Получаем тестовый логгер
    logger = get_logger(service_name)
    
    # Проверяем создание директорий
    current_month = datetime.now().strftime('%Y-%m')
    service_log_dir = Path('logs') / service_name / current_month
    assert service_log_dir.exists()
    
    # Проверяем создание файлов логов
    service_log = service_log_dir / 'service.log'
    error_log = service_log_dir / 'error.log'
    debug_log = service_log_dir / 'debug.log'
    
    assert service_log.exists()
    assert error_log.exists()
    assert debug_log.exists()
    
    # Пишем тестовые сообщения разных уровней
    test_messages = {
        'debug': "Test debug message",
        'info': "Test info message",
        'error': "Test error message"
    }
    
    logger.debug(test_messages['debug'])
    logger.info(test_messages['info'])
    logger.error(test_messages['error'])
    
    # Проверяем запись в файлы
    with open(service_log, 'r') as f:
        content = f.read()
        assert test_messages['info'] in content
        assert test_messages['error'] in content
    
    with open(error_log, 'r') as f:
        content = f.read()
        assert test_messages['error'] in content
        assert test_messages['info'] not in content
    
    with open(debug_log, 'r') as f:
        content = f.read()
        assert all(msg in content for msg in test_messages.values())

def test_log_rotation(cleanup_logs):
    """Тест ротации логов"""
    service_name = 'test_rotation'
    
    # Настраиваем логирование
    setup_logging(service_name)
    logger = get_logger(service_name)
    
    # Генерируем большое количество логов
    large_message = "X" * 1024  # 1KB сообщение
    for _ in range(11000):  # Должно создать более 10MB логов
        logger.info(large_message)
    
    # Проверяем создание файлов ротации
    current_month = datetime.now().strftime('%Y-%m')
    service_log_dir = Path('logs') / service_name / current_month
    
    rotation_files = list(service_log_dir.glob('service.log.*'))
    assert len(rotation_files) > 0, "Должны быть созданы файлы ротации"

def test_multiple_services(cleanup_logs):
    """Тест логирования нескольких сервисов"""
    services = ['service1', 'service2']
    loggers = {}
    
    # Настраиваем логирование для каждого сервиса
    for service in services:
        setup_logging(service)
        loggers[service] = get_logger(service)
    
    # Пишем сообщения от разных сервисов
    messages = {
        'service1': "Message from service 1",
        'service2': "Message from service 2"
    }
    
    for service, message in messages.items():
        loggers[service].info(message)
    
    # Проверяем, что сообщения попали в правильные файлы
    current_month = datetime.now().strftime('%Y-%m')
    
    for service in services:
        log_file = Path('logs') / service / current_month / 'service.log'
        with open(log_file, 'r') as f:
            content = f.read()
            assert messages[service] in content
            assert all(msg not in content for srv, msg in messages.items() if srv != service)

def test_error_handling(cleanup_logs):
    """Тест обработки ошибок при логировании"""
    service_name = 'test_errors'
    
    # Настраиваем логирование
    setup_logging(service_name)
    logger = get_logger(service_name)
    
    # Создаем тестовое исключение
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error("Error occurred", exc_info=True)
    
    # Проверяем запись стека вызовов
    current_month = datetime.now().strftime('%Y-%m')
    error_log = Path('logs') / service_name / current_month / 'error.log'
    
    with open(error_log, 'r') as f:
        content = f.read()
        assert "Error occurred" in content
        assert "ValueError: Test error" in content
        assert "Traceback" in content 