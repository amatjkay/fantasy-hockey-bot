import logging
from src.config.settings import LOG_FILE

def setup_logging():
    """Настройка логирования
    
    Настраивает логирование с записью в файл и выводом в консоль.
    Уровень логирования: INFO
    Формат: [время] - [уровень] - [сообщение]
    """
    # Создаем форматтер для логов
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настраиваем логирование в файл
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # Настраиваем вывод в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Очищаем существующие обработчики
    root_logger.handlers = []
    
    # Добавляем наши обработчики
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logging.info("Логирование настроено")
