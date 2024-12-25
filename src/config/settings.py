import os
import pytz
from pathlib import Path
from datetime import datetime

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
TEMP_DIR = DATA_DIR / "temp"  # Директория для временных файлов
CACHE_DIR = DATA_DIR / "cache"  # Директория для кэша
RAW_DIR = DATA_DIR / "raw"  # Директория для сырых данных
PROCESSED_DIR = DATA_DIR / "processed"  # Директория для обработанных данных

# Файлы
LOG_FILE = LOGS_DIR / "app.log"
PLAYER_STATS_FILE = PROCESSED_DIR / "player_stats.json"
LAST_RUN_FILE = LOGS_DIR / "last_run.log"
WEEK_LOG_FILE = LOGS_DIR / "week_log.txt"
DAY_LOG_FILE = LOGS_DIR / "day_log.txt"

# Временная зона
try:
    ESPN_TIMEZONE = pytz.timezone('US/Eastern')
except pytz.exceptions.UnknownTimeZoneError:
    ESPN_TIMEZONE = pytz.timezone('America/New_York')

# ESPN API
ESPN_API = {
    'SEASON_START_DATE': datetime(2024, 10, 4, tzinfo=ESPN_TIMEZONE),
    'SEASON_START_SCORING_PERIOD_ID': 1,
    'LEAGUE_ID': 484910394,
    'BASE_URL': 'https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl',
    'SEASON': '2025',
    'HEADERS': {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0',
    },
    'TIMEOUT': 10,
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 2,
}

# Формируем URL для API
API_URL_TEMPLATE = f"{ESPN_API['BASE_URL']}/seasons/{ESPN_API['SEASON']}/segments/0/leagues/{{league_id}}?view=kona_player_info&scoringPeriodId={{scoring_period_id}}"

# Позиции игроков и их лимиты
POSITION_MAP = {
    'C': 1,   # Центральный нападающий
    'LW': 1,  # Левый крайний нападающий
    'RW': 1,  # Правый крайний нападающий
    'D': 2,   # Защитники
    'G': 1    # Вратарь
}

# Цвета и грейды
GRADES = {
    "common": {
        "color": "black",
        "min_appearances": 1
    },
    "uncommon": {
        "color": "green",
        "min_appearances": 2
    },
    "rare": {
        "color": "blue",
        "min_appearances": 3
    },
    "epic": {
        "color": "purple",
        "min_appearances": 4
    },
    "legend": {
        "color": "orange",
        "min_appearances": 5
    }
}

GRADE_COLORS = {grade: info["color"] for grade, info in GRADES.items()}

# Настройки изображений
IMAGE_SETTINGS = {
    'PLAYER': {
        'WIDTH': 130,
        'HEIGHT': 100,
    },
    'PADDING': 20,
    'TEXT_PADDING': 10,
    'COLLAGE_WIDTH': 500,
}

# Создание необходимых директорий
for directory in [LOGS_DIR, DATA_DIR, TEMP_DIR, CACHE_DIR, RAW_DIR, PROCESSED_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

def load_env_vars():
    """Загрузка и проверка переменных окружения
    
    Returns:
        dict: Словарь с переменными окружения
        
    Raises:
        ValueError: Если отсутствуют обязательные переменные окружения
    """
    required_vars = {
        'TELEGRAM_TOKEN': os.getenv('TELEGRAM_TOKEN'),
        'CHAT_ID': os.getenv('CHAT_ID'),
        'ESPN_SWID': os.getenv('ESPN_SWID'),
        'ESPN_S2': os.getenv('ESPN_S2')
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
    
    return required_vars
