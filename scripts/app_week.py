#!/usr/bin/env python3
import argparse
from datetime import datetime, timedelta
from src.services.stats_service import StatsService
from src.services.image_service import ImageService
from src.services.telegram_service import TelegramService
from src.utils.logging import setup_logging

def parse_args() -> argparse.Namespace:
    """Разбор аргументов командной строки
    
    Returns:
        argparse.Namespace: Аргументы командной строки
    """
    parser = argparse.ArgumentParser(description='Формирование команды недели')
    
    # Аргумент для даты
    parser.add_argument(
        '--week',
        type=lambda s: datetime.strptime(s, '%Y-%m-%d'),
        help='Дата в формате YYYY-MM-DD',
        required=True
    )
    
    # Флаг для отключения отправки в Telegram
    parser.add_argument(
        '--no-send',
        action='store_true',
        help='Не отправлять результаты в Telegram'
    )
    
    return parser.parse_args()

def get_week_dates(date: datetime) -> tuple[datetime, datetime]:
    """Получение дат начала и конца недели
    
    Args:
        date (datetime): Дата
        
    Returns:
        tuple[datetime, datetime]: Даты начала и конца недели
    """
    # Получаем начало недели (понедельник)
    start_date = date - timedelta(days=date.weekday())
    
    # Получаем конец недели (воскресенье)
    end_date = start_date + timedelta(days=6)
    
    return start_date, end_date

def main():
    """Основная функция"""
    try:
        # Инициализация логирования
        logger = setup_logging('app_week')
        logger.info("Запуск формирования команды недели")
        
        # Разбор аргументов
        args = parse_args()
        
        # Получаем даты недели
        start_date, end_date = get_week_dates(args.week)
        
        # Инициализация сервисов
        stats_service = StatsService()
        image_service = ImageService()
        telegram_service = TelegramService()
        
        # Получаем команду недели
        team = stats_service.get_team_of_the_week(start_date, end_date)
        if not team:
            logger.error("Не удалось получить команду недели")
            return
            
        # Формируем заголовок
        title = f"Команда недели {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
            
        # Создаем коллаж
        collage_path = image_service.create_team_collage(team, title)
        if not collage_path:
            logger.error("Не удалось создать коллаж")
            return
            
        # Отправляем в Telegram если нужно
        if not args.no_send:
            telegram_service.send_team_of_the_week(collage_path)
            
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        raise

if __name__ == '__main__':
    main() 