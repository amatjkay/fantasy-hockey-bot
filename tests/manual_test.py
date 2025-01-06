from datetime import datetime
import logging
from src.services.team_service import TeamService
from src.services.stats_service import StatsService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_full_pipeline():
    """Тестирование полного процесса"""
    date = datetime(2024, 10, 4)  # Первый день сезона
    
    # Тестируем получение статистики
    stats_service = StatsService()
    daily_stats = stats_service.get_daily_stats(date)
    logger.info(f"Получена статистика: {bool(daily_stats)}")
    
    if daily_stats:
        # Тестируем формирование команды
        team_service = TeamService()
        team = team_service.get_team_of_day(date)
        logger.info(f"Сформирована команда: {bool(team)}")
        
        if team:
            logger.info(f"Количество игроков: {len(team['players'])}")
            logger.info(f"Общие очки: {team['total_points']}")
            
            # Тестируем создание коллажа
            collage_path = team_service.create_team_collage(team)
            logger.info(f"Создан коллаж: {bool(collage_path)}")
            if collage_path:
                logger.info(f"Путь к коллажу: {collage_path}")

if __name__ == '__main__':
    test_full_pipeline() 