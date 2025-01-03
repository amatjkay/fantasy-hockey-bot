import os
from dotenv import load_dotenv
from .settings import SEASON, LEAGUE_ID

load_dotenv()

# ESPN API
ESPN_API_KEY = os.getenv('ESPN_API_KEY')
ESPN_API_SECRET = os.getenv('ESPN_API_SECRET')
ESPN_BASE_URL = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"

# Telegram API
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Настройки запросов
REQUEST_TIMEOUT = 30  # секунды
MAX_RETRIES = 3
RETRY_DELAY = 5  # секунды

# Заголовки для ESPN API
ESPN_HEADERS = {
    'X-Fantasy-Source': 'kona',
    'X-Fantasy-Filter': '{"players":{"filterStatus":{"value":["FREEAGENT","WAIVERS","ONTEAM"]},"filterSlotIds":{"value":[0,1,2,3,4,5,6]}}}',
}

# Параметры запросов к ESPN API
ESPN_PARAMS = {
    'scoringPeriodId': None,  # Будет установлено при запросе
    'view': ['kona_player_info', 'mStats', 'mInfo', 'mRoster']
} 