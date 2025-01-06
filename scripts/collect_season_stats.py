#!/usr/bin/env python3
import os
import sys
import logging
import argparse
from datetime import datetime
import pytz
from src.services.stats_service import StatsService
from src.config.settings import ESPN_TIMEZONE, PROCESSED_DATA_DIR
import json

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def parse_date(date_str: str) -> datetime:
    """Преобразует строку даты в объект datetime"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        return ESPN_TIMEZONE.localize(date)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Неверный формат даты: {str(e)}")

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Сбор статистики за период')
    parser.add_argument('--start-date', type=str, help='Начальная дата (YYYY-MM-DD)', required=True)
    parser.add_argument('--end-date', type=str, help='Конечная дата (YYYY-MM-DD)', required=True)
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Создаем сервис
        stats_service = StatsService()
        
        # Преобразуем даты
        start_date = parse_date(args.start_date)
        end_date = parse_date(args.end_date)
        
        # Собираем статистику
        stats = stats_service.collect_season_stats(
            start_date=start_date,
            end_date=end_date
        )
        
        if not stats:
            logger.error("Не удалось собрать статистику")
            sys.exit(1)
            
        # Сохраняем результаты
        output_file = os.path.join(PROCESSED_DATA_DIR, 'season_stats.json')
        with open(output_file, 'w') as f:
            json.dump(stats, f, indent=2)
            
        logger.info(f"Статистика успешно сохранена в {output_file}")
        logger.info(f"Обработано дней: {stats['total_days']}")
        
    except Exception as e:
        logger.error(f"Ошибка выполнения скрипта: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 