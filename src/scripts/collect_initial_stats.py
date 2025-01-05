import os
import json
import logging
from datetime import datetime, timedelta
from src.services.stats_service import StatsService
from src.config.settings import ESPN_API, ESPN_TIMEZONE, PROCESSED_DATA_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def collect_season_stats():
    """Собирает статистику за весь сезон"""
    stats_service = StatsService()
    
    # Получаем начальную и конечную даты сезона
    season_start = ESPN_API['SEASON_START_DATE']
    if isinstance(season_start, str):
        season_start = datetime.strptime(season_start, '%Y-%m-%d')
        season_start = ESPN_TIMEZONE.localize(season_start)
    elif season_start.tzinfo is None:
        season_start = ESPN_TIMEZONE.localize(season_start)
    else:
        season_start = season_start.astimezone(ESPN_TIMEZONE)
    
    today = datetime.now(ESPN_TIMEZONE)
    
    # Создаем структуру для хранения статистики
    season_stats = {
        'start_date': season_start.strftime('%Y-%m-%d'),
        'end_date': today.strftime('%Y-%m-%d'),
        'daily_stats': [],
        'weekly_stats': []
    }
    
    # Собираем статистику по дням
    current_date = season_start
    while current_date <= today:
        logger.info(f"Собираем статистику за {current_date.strftime('%Y-%m-%d')}")
        
        daily_stats = stats_service.collect_stats(current_date)
        if daily_stats:
            season_stats['daily_stats'].append(daily_stats)
            
        current_date += timedelta(days=1)
    
    # Собираем недельную статистику
    current_date = season_start
    while current_date <= today:
        logger.info(f"Собираем недельную статистику с {current_date.strftime('%Y-%m-%d')}")
        
        weekly_stats = stats_service.collect_weekly_stats(current_date)
        if weekly_stats:
            season_stats['weekly_stats'].append(weekly_stats)
            
        current_date += timedelta(days=7)
    
    # Сохраняем результаты
    stats_file = os.path.join(PROCESSED_DATA_DIR, 'season_stats.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(season_stats, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Статистика сохранена в {stats_file}")
    return season_stats

if __name__ == '__main__':
    collect_season_stats() 