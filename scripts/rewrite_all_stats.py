#!/usr/bin/env python3

import sys
import os
import logging
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.espn_service import ESPNService
from scripts.send_daily_teams import (
    load_history,
    save_history,
    get_best_players_by_position,
    update_history
)

def setup_logging():
    """Настройка логирования"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file = os.path.join(log_dir, f"rewrite_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def get_date_range():
    """Получение диапазона дат для обработки"""
    # Начало сезона - 4 октября 2024
    start_date = datetime(2024, 10, 4, tzinfo=pytz.UTC)
    # Конец - вчерашний день
    end_date = datetime.now(pytz.UTC) - timedelta(days=1)
    
    return start_date, end_date

def process_date(date, espn_service, history, logger):
    """Обработка одной даты"""
    try:
        date_str = date.strftime('%Y-%m-%d')
        logger.info(f"Обработка даты: {date_str}")
        
        # Получаем статистику за день
        daily_stats = espn_service.get_daily_stats(date)
        
        if not daily_stats:
            logger.warning(f"Нет статистики для даты {date_str}")
            return
            
        # Формируем команду из лучших игроков
        team = get_best_players_by_position(daily_stats, date_str, history)
        
        if not team:
            logger.warning(f"Не удалось сформировать команду для даты {date_str}")
            return
            
        # Обновляем историю
        update_history(team, date_str, history)
        logger.info(f"Статистика успешно обновлена для даты {date_str}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке даты {date_str}: {e}")

def main():
    """Основная функция"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Загружаем переменные окружения
        load_dotenv()
        
        # Инициализируем сервисы
        espn_service = ESPNService()
        
        # Загружаем текущую историю
        history = load_history()
        
        # Получаем диапазон дат
        start_date, end_date = get_date_range()
        
        # Обрабатываем каждую дату
        current_date = start_date
        while current_date <= end_date:
            process_date(current_date, espn_service, history, logger)
            current_date += timedelta(days=1)
            
        logger.info("Обработка всех дат завершена")
        
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 