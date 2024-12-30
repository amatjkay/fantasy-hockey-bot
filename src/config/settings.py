import os
from pathlib import Path
import pytz
from datetime import datetime
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
TEMP_DIR = DATA_DIR / "temp"
CACHE_DIR = DATA_DIR / "cache"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
LOG_DIR = BASE_DIR / "logs"

# Создаем директории, если они не существуют
for dir_path in [TEMP_DIR, CACHE_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, LOG_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Настройки временной зоны
ESPN_TIMEZONE = pytz.timezone(os.getenv('TIMEZONE', 'US/Eastern'))
DAY_START_HOUR = int(os.getenv('DAY_START_HOUR', '4'))

# Настройки сезона
SEASON_START_DATE = datetime.strptime(os.getenv('SEASON_START', '2024-10-04'), '%Y-%m-%d').replace(tzinfo=ESPN_TIMEZONE)
SEASON_START_SCORING_PERIOD = int(os.getenv('SEASON_START_SCORING_PERIOD', '1'))

# Настройки ESPN API
ESPN_API = {
    'swid': os.getenv('ESPN_SWID'),
    's2': os.getenv('ESPN_S2'),
    'season_id': os.getenv('SEASON_ID', '2025'),
    'league_id': os.getenv('LEAGUE_ID'),
    'HEADERS': {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json'
    },
    'TIMEOUT': 30,
    'SEASON_START_DATE': SEASON_START_DATE,
    'SEASON_START_SCORING_PERIOD_ID': SEASON_START_SCORING_PERIOD
}

# URL шаблон для ESPN API
API_URL_TEMPLATE = "https://fantasy.espn.com/apis/v3/games/fhl/seasons/{season_id}/segments/0/leagues/{league_id}?view=mRoster&scoringPeriodId={scoring_period_id}"

# Пути к файлам данных
PLAYER_STATS_FILE = PROCESSED_DATA_DIR / "player_stats.json"
WEEKLY_TEAM_STATS_FILE = PROCESSED_DATA_DIR / "weekly_team_stats.json"
SCHEDULE_FILE = RAW_DATA_DIR / "TeamSchedules.json"
LEAGUE_SETTINGS_FILE = RAW_DATA_DIR / "LeagueSettings.json"

# Настройки позиций
POSITION_MAP = {
    'C': 1,
    'LW': 1,
    'RW': 1,
    'D': 2,
    'G': 1
}

# Настройки грейдов
GRADE_COLORS = {
    "common": "black",     # обычный
    "uncommon": "green",   # необычный
    "rare": "blue",        # редкий
    "epic": "purple",      # эпический
    "legend": "orange"     # легендарный
}

# Настройки изображений
IMAGE_SETTINGS = {
    'PLAYER': {
        'WIDTH': 130,
        'HEIGHT': 100,
    },
    'PADDING': 20,
    'TEXT_PADDING': 10,
    'COLLAGE_WIDTH': 500,
    'FONT_SIZE': 20,
    'TITLE_FONT_SIZE': 24,
    'LINE_HEIGHT': 150,  # Высота строки с учетом изображения и текста
    'BACKGROUND_COLOR': 'white',
    'TEXT_COLOR': 'black',
    'FONT_PATHS': [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf"
    ]
}

# Настройки для формирования команд
TEAM_SETTINGS = {
    'players_in_team': 5,  # Количество игроков в команде
    'min_minutes_played': 10,  # Минимальное количество сыгранных минут
    'stats_weights': {
        'points': 1.0,
        'rebounds': 0.7,
        'assists': 0.7,
        'steals': 1.2,
        'blocks': 1.2,
        'turnovers': -0.5
    }
}

def load_env_vars():
    """Загрузка и проверка переменных окружения"""
    required_vars = {
        'TELEGRAM_TOKEN': os.getenv('TELEGRAM_TOKEN'),
        'CHAT_ID': os.getenv('CHAT_ID'),
        'ESPN_SWID': ESPN_API['swid'],
        'ESPN_S2': ESPN_API['s2'],
        'LEAGUE_ID': ESPN_API['league_id']
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
        
    return required_vars
