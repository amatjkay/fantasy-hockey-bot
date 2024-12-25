import os
import pytz
from pathlib import Path

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

# Файлы
LOG_FILE = LOGS_DIR / "app.log"
PLAYER_STATS_FILE = DATA_DIR / "player_stats.json"

# Временная зона
try:
    ESPN_TIMEZONE = pytz.timezone('US/Eastern')
except pytz.exceptions.UnknownTimeZoneError:
    ESPN_TIMEZONE = pytz.timezone('America/New_York')  # Альтернативное название той же зоны

# ESPN API
SEASON_START_DATE = "2024-10-04"
SEASON_START_SCORING_PERIOD_ID = 1
LEAGUE_ID = 484910394
API_URL_TEMPLATE = 'https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/2025/segments/0/leagues/{league_id}?view=kona_player_info'

# Позиции игроков
POSITION_MAP = {
    'C': 1,
    'LW': 1,
    'RW': 1,
    'D': 2,
    'G': 1
}

# Цвета для грейдов
GRADE_COLORS = {
    "common": "black",
    "uncommon": "green",
    "rare": "blue",
    "epic": "purple",
    "legend": "orange"
}

# Создание необходимых директорий
for directory in [LOGS_DIR, DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Загрузка переменных окружения
def load_env_vars():
    """Загрузка и проверка переменных окружения"""
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not telegram_token or not chat_id:
        raise ValueError("TELEGRAM_TOKEN или CHAT_ID не установлены в файле .env")
    
    return {
        'TELEGRAM_TOKEN': telegram_token,
        'CHAT_ID': chat_id
    }
