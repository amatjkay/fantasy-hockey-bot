import os
from dotenv import load_dotenv
from typing import Dict

load_dotenv()

# ESPN API
ESPN_SWID = os.getenv('ESPN_SWID')
ESPN_S2 = os.getenv('ESPN_S2')
ESPN_BASE_URL = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/{season}/segments/0/leagues/{league_id}"

# Telegram API
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Настройки запросов
REQUEST_TIMEOUT = 10  # секунды
MAX_RETRIES = 3
RETRY_DELAY = 5  # секунды

# Заголовки для ESPN API
DEFAULT_HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'x-fantasy-source': 'kona',
    'x-fantasy-platform': 'kona-PROD-6daa0c838b3e2ff0192c0d7d1d24be52e5053a91',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    '_cb': 'Cx48e6DC1aoIBj-OxU',
    'device_61726d61': 'e63e04f7-311e-4205-962a-94562f7435d1',
    'ESPN-ONESITE.WEB-PROD.api': 'fXXStqDrRau2rAnprLnbZHeAtVy9ipGJJqh6isuJptgyJA9uP+blVmTpv5VGuE6ys1ByXs9VoMzz878BGFSlNbZlcbEX'
}

def get_player_filter(scoring_period_id: int, slot_ids: list = [0,1,2,3,4,6]) -> Dict:
    return {
        "players": {
            "filterSlotIds": {
                "value": slot_ids
            },
            "filterStatsForCurrentSeasonScoringPeriodId": {
                "value": [scoring_period_id]
            },
            "sortPercOwned": {
                "sortPriority": 3,
                "sortAsc": False
            },
            "limit": 50,
            "offset": 0,
            "sortAppliedStatTotalForScoringPeriodId": {
                "sortAsc": False,
                "sortPriority": 1,
                "value": scoring_period_id
            },
            "filterRanksForScoringPeriodIds": {
                "value": [scoring_period_id]
            },
            "filterRanksForRankTypes": {
                "value": ["STANDARD"]
            }
        }
    }

POSITION_MAP = {
    1: 'C',   # Center
    2: 'LW',  # Left Wing
    3: 'RW',  # Right Wing
    4: 'D',   # Defense
    5: 'G'    # Goalie
} 