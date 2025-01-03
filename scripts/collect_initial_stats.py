#!/usr/bin/env python3
import os
import sys
import argparse
from datetime import datetime, timedelta
import pytz
from typing import Optional, List, Tuple

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import setup_logging, TIMEZONE
from src.services.stats_service import StatsService

def parse_args():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description='Сбор начальной статистики')
    parser.add_argument(
        '--start-date',
        type=str,
        help='Дата начала сбора в формате YYYY-MM-DD (по умолчанию - начало сезона)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='Дата конца сбора в формате YYYY-MM-DD (по умолчанию - вчера)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Принудительное обновление существующих данных'
    )
    return parser.parse_args()

def get_date_range(start_date_str: Optional[str], end_date_str: Optional[str]) -> Tuple[datetime, datetime]:
    """Получение диапазона дат для сбора статистики
    
    Args:
        start_date_str (str, optional): Строка с начальной датой
        end_date_str (str, optional): Строка с конечной датой
        
    Returns:
        Tuple[datetime, datetime]: Кортеж из начальной и конечной дат
    """
    tz = pytz.timezone(TIMEZONE)
    
    # Определяем конечную дату (вчера)
    end_date = datetime.now(tz) - timedelta(days=1)
    if end_date_str:
        end_date = tz.localize(datetime.strptime(end_date_str, '%Y-%m-%d'))
    
    # Определяем начальную дату (начало сезона - 4 октября 2024)
    start_date = tz.localize(datetime(2024, 10, 4))
    if start_date_str:
        start_date = tz.localize(datetime.strptime(start_date_str, '%Y-%m-%d'))
    
    return start_date, end_date

def get_dates_to_process(start_date: datetime, end_date: datetime) -> List[datetime]:
    """Получение списка дат для обработки
    
    Args:
        start_date (datetime): Начальная дата
        end_date (datetime): Конечная дата
        
    Returns:
        List[datetime]: Список дат для обработки
    """
    dates = []
    current_date = start_date
    
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    return dates

def main():
    """Основная функция скрипта"""
    # Настраиваем логирование
    logger = setup_logging('collect_stats')
    logger.info('Запуск сбора начальной статистики')
    
    try:
        # Парсим аргументы
        args = parse_args()
        start_date, end_date = get_date_range(args.start_date, args.end_date)
        
        # Получаем список дат для обработки
        dates = get_dates_to_process(start_date, end_date)
        total_dates = len(dates)
        
        logger.info(f'Сбор статистики с {start_date.date()} по {end_date.date()} ({total_dates} дней)')
        
        # Инициализируем сервис
        stats_service = StatsService()
        
        # Обрабатываем каждую дату
        for i, date in enumerate(dates, 1):
            logger.info(f'Обработка даты {date.date()} ({i}/{total_dates})')
            
            # Получаем команду дня
            team = stats_service.get_team_of_the_day(date)
            if not team:
                logger.warning(f'Нет данных за {date.date()}')
                continue
            
            # Обновляем грейды после каждой недели
            if date.weekday() == 6:  # Воскресенье
                stats_service.update_player_grades()
        
        logger.info('Сбор статистики завершен успешно')
        return 0
        
    except Exception as e:
        logger.error(f'Неожиданная ошибка: {e}', exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main()) 