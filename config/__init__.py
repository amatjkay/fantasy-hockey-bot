import os
import logging
from dotenv import load_dotenv

# Настройки логирования
import logging
logging.basicConfig(level=logging.DEBUG)

# Загружаем переменные окружения
load_dotenv()

# Настройки ESPN API
ESPN_BASE_URL = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons"
ESPN_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "x-fantasy-source": "kona",
    "x-fantasy-platform": "kona-PROD-12e764fad9fd0892caaf6ac5e9ec6893895afdb8"
}

# Фильтры для запросов
ESPN_FILTERS = {
    "goalies": {
        "players": {
            "filterSlotIds": {"value": [5]},
            "limit": 50,
            "offset": 0,
            "sortPercOwned": {"sortPriority": 3, "sortAsc": False},
            "filterRanksForRankTypes": {"value": ["STANDARD"]}
        }
    },
    "skaters": {
        "players": {
            "filterSlotIds": {"value": [0,1,2,3,4,6]},
            "limit": 50,
            "offset": 0,
            "sortPercOwned": {"sortPriority": 3, "sortAsc": False},
            "filterRanksForRankTypes": {"value": ["STANDARD"]}
        }
    }
}

# Настройки сезона и лиги
SEASON = os.getenv('SEASON_ID', '2025')
LEAGUE_ID = os.getenv('LEAGUE_ID', '484910394')

# Настройки Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

# Настройки временной зоны
TIMEZONE = os.getenv('TIMEZONE', 'US/Eastern')
DAY_START_HOUR = int(os.getenv('DAY_START_HOUR', '4'))

# Настройки запросов
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 5

# Пути к файлам
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
PLAYER_STATS_FILE = os.path.join(DATA_DIR, 'processed', 'player_stats.json')
SEASON_STATS_FILE = os.path.join(DATA_DIR, 'processed', 'season_stats.json')
TEAMS_HISTORY_FILE = os.path.join(DATA_DIR, 'processed', 'teams_history.json')
WEEKLY_TEAM_STATS_FILE = os.path.join(DATA_DIR, 'processed', 'weekly_team_stats.json')

# Настройки изображений
PLAYER_IMAGE_SIZE = (130, 100)
PLAYER_IMAGES_CACHE = os.path.join(DATA_DIR, 'cache', 'player_images')
TEMP_DIR = os.path.join(DATA_DIR, 'temp')
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')

def setup_logging(name: str = None) -> logging.Logger:
    """Настройка логирования
    
    Args:
        name (str, optional): Имя логгера
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    # Создаем директорию для логов
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Настраиваем формат
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Создаем обработчики
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f'{name if name else "app"}.log')
    )
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Настраиваем логгер
    logger = logging.getLogger(name if name else 'app')
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 