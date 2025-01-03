#!/usr/bin/env python3
import os
import sys
import argparse
from datetime import datetime
import pytz
from typing import Optional

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import setup_logging, TIMEZONE, OUTPUT_DIR
from src.services.stats_service import StatsService
from src.services.image_service import ImageService
from src.services.telegram_service import TelegramService

def parse_args() -> argparse.Namespace:
    """Разбор аргументов командной строки
    
    Returns:
        argparse.Namespace: Аргументы командной строки
    """
    parser = argparse.ArgumentParser(description='Формирование команды дня')
    
    # Аргумент для даты
    parser.add_argument(
        '--date',
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

def get_date(date_str: Optional[str] = None) -> datetime:
    """Получение даты из строки или текущей даты
    
    Args:
        date_str (str, optional): Строка с датой в формате YYYY-MM-DD
        
    Returns:
        datetime: Объект даты
    """
    if date_str:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    else:
        date = datetime.now()
    
    # Приводим к нужному часовому поясу
    tz = pytz.timezone(TIMEZONE)
    return tz.localize(date)

def main():
    """Основная функция"""
    try:
        # Инициализация логирования
        logger = setup_logging('app_day')
        logger.info("Запуск формирования команды дня")
        
        # Разбор аргументов
        args = parse_args()
        
        # Инициализация сервисов
        stats_service = StatsService()
        image_service = ImageService()
        telegram_service = TelegramService()
        
        # Получаем команду дня
        team = stats_service.get_team_of_the_day(args.date)
        if not team:
            logger.error("Не удалось получить команду дня")
            return
            
        # Формируем заголовок
        title = f"Команда дня {args.date.strftime('%d.%m.%Y')}"
            
        # Создаем коллаж
        collage_path = image_service.create_team_collage(team, title)
        if not collage_path:
            logger.error("Не удалось создать коллаж")
            return
            
        # Отправляем в Telegram если нужно
        if not args.no_send:
            telegram_service.send_team_of_the_day(collage_path)
            
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        raise

if __name__ == '__main__':
    sys.exit(main())
