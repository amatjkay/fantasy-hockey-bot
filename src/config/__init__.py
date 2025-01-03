import os
import logging
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Пути к директориям
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
PHOTOS_DIR = os.path.join(DATA_DIR, 'photos')
COLLAGES_DIR = os.path.join(DATA_DIR, 'collages')

# Создаем директории если не существуют
for directory in [DATA_DIR, PROCESSED_DIR, PHOTOS_DIR, COLLAGES_DIR]:
    os.makedirs(directory, exist_ok=True)

# Настройки ESPN API
ESPN_BASE_URL = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/2025/segments/0/leagues/484910394"
ESPN_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "X-Fantasy-Source": "kona",
    "X-Fantasy-Filter": None
}

# Настройки сезона
SEASON = os.getenv('SEASON', '2024')
LEAGUE_ID = os.getenv('LEAGUE_ID', '12345')

# Настройки Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Настройки времени
TIMEZONE = 'America/New_York'

# Маппинг позиций
POSITION_MAPPING = {
    1: 'C',   # Center
    2: 'LW',  # Left Wing
    3: 'RW',  # Right Wing
    4: 'D',   # Defense
    5: 'G'    # Goalie
}

# Маппинг грейдов
GRADE_MAPPING = {
    'common': 0,
    'rare': 1,
    'epic': 2,
    'legendary': 3
}

# Пути к файлам данных
TEAMS_HISTORY_FILE = os.path.join(PROCESSED_DIR, 'teams_history.json')
PLAYER_GRADES_FILE = os.path.join(PROCESSED_DIR, 'player_grades.json')

def get_fantasy_filter(start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
    """Получение фильтра для ESPN API
    
    Args:
        start_date (Optional[datetime]): Начальная дата
        end_date (Optional[datetime]): Конечная дата
        
    Returns:
        Dict: Фильтр для API
    """
    filter_dict = {
        "players": {
            "filterStatsForExternalIds": {
                "value": [int(SEASON)]
            }
        }
    }
    
    if start_date and end_date:
        filter_dict["players"]["filterStatsForDateRange"] = {
            "value": [
                int(start_date.timestamp() * 1000),
                int(end_date.timestamp() * 1000)
            ]
        }
        
    return filter_dict
