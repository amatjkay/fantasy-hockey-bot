import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Загружаем переменные окружения из .env
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
CACHE_DIR = DATA_DIR / 'cache'
LOGS_DIR = BASE_DIR / 'logs'

# Создаем необходимые директории
for directory in [DATA_DIR, PROCESSED_DIR, CACHE_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Настройки ESPN API
ESPN_API = {
    'swid': os.getenv('ESPN_SWID'),
    's2': os.getenv('ESPN_S2'),
    'league_id': os.getenv('LEAGUE_ID'),
    'season_id': os.getenv('SEASON_ID'),
    'SEASON_START_DATE': datetime.strptime(os.getenv('SEASON_START', '2024-10-04'), '%Y-%m-%d'),
    'SEASON_START_SCORING_PERIOD_ID': 1,
    'TIMEOUT': 30,
    'HEADERS': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'X-Fantasy-Source': 'kona',
        'X-Fantasy-Platform': 'fantasy-hockey',
        'X-Fantasy-Filter': '{"players":{"filterStatus":{"value":["FREEAGENT","WAIVERS","ONTEAM"]},"filterSlotIds":{"value":[0,1,2,3,4,5,6]}}}',
        'Origin': 'https://fantasy.espn.com',
        'Referer': 'https://fantasy.espn.com/hockey/team',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
}

# Настройки временной зоны
ESPN_TIMEZONE = 'America/New_York'

# Настройки Telegram
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') 