import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / os.getenv('DATA_DIR', 'data/processed')
CACHE_DIR = BASE_DIR / os.getenv('CACHE_DIR', 'data/cache')
TEMP_DIR = BASE_DIR / os.getenv('TEMP_DIR', 'data/temp')
OUTPUT_DIR = BASE_DIR / os.getenv('OUTPUT_DIR', 'data/output')
LOGS_DIR = BASE_DIR / os.getenv('LOGS_DIR', 'logs')

# Настройки сезона
SEASON = os.getenv('SEASON', '2025')
LEAGUE_ID = os.getenv('LEAGUE_ID', '484910394')
TIMEZONE = os.getenv('TIMEZONE', 'US/Eastern')

# Файлы данных
PLAYER_STATS_FILE = DATA_DIR / 'player_stats.json'
SEASON_STATS_FILE = DATA_DIR / 'season_stats.json'
TEAMS_HISTORY_FILE = DATA_DIR / 'teams_history.json'
WEEKLY_TEAM_STATS_FILE = DATA_DIR / 'weekly_team_stats.json'

# Настройки изображений
PLAYER_IMAGE_SIZE = (130, 100)
PLAYER_IMAGES_CACHE = CACHE_DIR / 'player_images'

# Создание директорий если они не существуют
for directory in [DATA_DIR, CACHE_DIR, TEMP_DIR, OUTPUT_DIR, LOGS_DIR, PLAYER_IMAGES_CACHE]:
    directory.mkdir(parents=True, exist_ok=True) 