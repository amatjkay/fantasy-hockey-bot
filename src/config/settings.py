import os
from pathlib import Path
import pytz
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
LOG_DIR = BASE_DIR / "logs"

# Создаем директории, если они не существуют
for dir_path in [CACHE_DIR, PROCESSED_DATA_DIR, LOG_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Файлы данных
STATS_FILE = PROCESSED_DATA_DIR / "player_stats.json"

# Настройки временной зоны
ESPN_TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "US/Eastern"))
DAY_START_HOUR = int(os.getenv("DAY_START_HOUR", "4"))

# Настройки сезона
SEASON_START = "2024-10-04"
SEASON_START_SCORING_PERIOD = 1

# Настройки ESPN API
ESPN_API = {
    'swid': os.getenv('ESPN_SWID'),
    's2': os.getenv('ESPN_S2'),
    'season_id': os.getenv('SEASON_ID', '2025'),
    'league_id': os.getenv('LEAGUE_ID'),
    'BASE_URL': f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/{os.getenv('SEASON_ID', '2025')}/segments/0/leagues/{os.getenv('LEAGUE_ID')}",
    'HEADERS': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/json',
        'X-Fantasy-Source': 'kona',
        'X-Fantasy-Platform': 'kona-PROD-12e764fad9fd0892caaf6ac5e9ec6893895afdb8',
        'Origin': 'https://fantasy.espn.com',
        'Referer': f'https://fantasy.espn.com/hockey/league?leagueId={os.getenv("LEAGUE_ID")}',
        'Cookie': f'SWID={os.getenv("ESPN_SWID")}; espn_s2={os.getenv("ESPN_S2")}',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    },
    'PARAMS': {
        'view': ['kona_player_info'],
        'scoringPeriodId': None  # Будет установлено динамически
    },
    'TIMEOUT': int(os.getenv("REQUEST_TIMEOUT", "30")),
    'RETRY_COUNT': int(os.getenv("MAX_RETRIES", "3")),
    'RETRY_DELAY': int(os.getenv("RETRY_DELAY", "5"))
}

# Настройки Telegram
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Позиции игроков
PLAYER_POSITIONS = {
    1: 'C',   # Center
    2: 'LW',  # Left Wing
    3: 'RW',  # Right Wing
    4: 'D',   # Defense
    5: 'G'    # Goalie
}

# Состав команды дня
TEAM_OF_DAY_COMPOSITION = {
    'C': 1,
    'LW': 1,
    'RW': 1,
    'D': 2,
    'G': 1
}

# Настройки запросов
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))

# Настройки кэширования
CACHE_TTL = 3600  # 1 час в секундах

# Пути к директориям
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets')

def load_env_vars():
    """Загрузка и проверка переменных окружения"""
    required_vars = {
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'CHAT_ID': TELEGRAM_CHAT_ID,
        'ESPN_SWID': ESPN_API['swid'],
        'ESPN_S2': ESPN_API['s2'],
        'LEAGUE_ID': ESPN_API['league_id']
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
        
    return required_vars
