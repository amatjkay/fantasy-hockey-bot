from dataclasses import dataclass
from typing import Dict
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

@dataclass
class ESPNConfig:
    base_url: str
    season_id: int
    league_id: int
    swid: str
    s2_token: str
    headers: Dict
    timezone: pytz.timezone

@dataclass
class Config:
    espn: ESPNConfig
    telegram_token: str
    telegram_chat_id: str
    data_dir: str = "data"
    cache_dir: str = "data/cache"
    photos_dir: str = "data/photos"
    collages_dir: str = "data/collages"
    processed_dir: str = "data/processed"

def load_config() -> Config:
    load_dotenv()
    
    espn_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "x-fantasy-source": "kona",
        "x-fantasy-platform": "kona-PROD-12e764fad9fd0892caaf6ac5e9ec6893895afdb8"
    }
    
    return Config(
        espn=ESPNConfig(
            base_url="https://fantasy.espn.com/apis/v3/games/fhl",
            season_id=int(os.getenv("SEASON", "2025")),
            league_id=int(os.getenv("LEAGUE_ID")),
            swid=os.getenv("ESPN_SWID"),
            s2_token=os.getenv("ESPN_S2"),
            headers=espn_headers,
            timezone=pytz.timezone('America/New_York')
        ),
        telegram_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID")
    ) 