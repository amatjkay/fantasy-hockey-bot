#!/usr/bin/env python3
import logging
from src.services.stats_service import StatsService
from config.logging_config import setup_logging
import json
import os
from config.settings import PROCESSED_DIR

def initialize_stats():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    stats_service = StatsService()
    
    # Создаем базовые файлы с пустой структурой
    base_structure = {
        "weeks": {},
        "players": {},
        "teams": {}
    }
    
    files = [
        "player_stats.json",
        "season_stats.json",
        "teams_history.json",
        "weekly_team_stats.json"
    ]
    
    for file in files:
        file_path = os.path.join(PROCESSED_DIR, file)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(base_structure, f, indent=2)
            logger.info(f"Created initial structure for {file}")

if __name__ == "__main__":
    initialize_stats() 