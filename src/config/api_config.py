"""
Конфигурация для работы с API
"""

import os
from dotenv import load_dotenv
from typing import Dict, List

# Загружаем переменные окружения
load_dotenv()

# ESPN API
ESPN_SWID = os.getenv('ESPN_SWID')
ESPN_S2 = os.getenv('ESPN_S2')
SEASON_ID = int(os.getenv('SEASON_ID', '2025'))

def get_api_season_id(season_id: int) -> int:
    """
    Преобразует ID сезона в формат API
    Например: 2024 -> 2025 (для текущего сезона)
    """
    return season_id + 1

ESPN_BASE_URL = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/{season}/segments/0/leagues/{league_id}"

# Настройки запросов
REQUEST_TIMEOUT = 10  # секунды
MAX_RETRIES = 3
RETRY_DELAY = 5  # секунды

# Маппинг позиций игроков
POSITION_MAP = {
    1: 'C',   # Center
    2: 'LW',  # Left Wing
    3: 'RW',  # Right Wing
    4: 'D',   # Defense
    5: 'G'    # Goalie
}

# Заголовки для ESPN API
DEFAULT_HEADERS = {
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'DNT': '1',
    'Host': 'lm-api-reads.fantasy.espn.com',
    'Origin': 'https://fantasy.espn.com',
    'Referer': 'https://fantasy.espn.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'x-fantasy-source': 'kona',
    'x-fantasy-filter': ''
}

def get_player_filter(scoring_period_id: int) -> dict:
    """Возвращает фильтр для получения статистики игроков"""
    return {
        "players": {
            "filterStatus": {
                "value": ["FREEAGENT", "WAIVERS", "ONTEAM"]
            },
            "filterSlotIds": {
                "value": [0, 1, 2, 3, 4, 5, 6]
            },
            "filterStatsForCurrentSeasonScoringPeriodId": {
                "value": [scoring_period_id]
            },
            "sortAppliedStatTotal": None,
            "sortAppliedStatTotalForScoringPeriodId": {
                "sortAsc": False,
                "sortPriority": 2,
                "value": scoring_period_id
            },
            "sortStatId": None,
            "sortStatIdForScoringPeriodId": None,
            "sortPercOwned": {
                "sortPriority": 3,
                "sortAsc": False
            },
            "limit": 50
        }
    } 