from typing import Dict, Optional
from datetime import datetime
import os
import json
import logging

logger = logging.getLogger(__name__)

class StatsCache:
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        self._ensure_cache_dir()
        
    def _ensure_cache_dir(self):
        """Создает директорию для кэша если она не существует"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
    def _get_cache_path(self, date: datetime) -> str:
        """Формирует путь к файлу кэша"""
        return os.path.join(
            self.cache_dir,
            f"stats_{date.strftime('%Y-%m-%d')}.json"
        )
        
    def get_cached_stats(self, date: datetime) -> Optional[Dict]:
        """Получает кэшированные данные"""
        cache_path = self._get_cache_path(date)
        
        if not os.path.exists(cache_path):
            return None
            
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка при чтении кэша: {e}")
            return None
            
    def cache_stats(self, date: datetime, stats: Dict):
        """Сохраняет данные в кэш"""
        cache_path = self._get_cache_path(date)
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(stats, f)
        except Exception as e:
            logger.error(f"Ошибка при сохранении в кэш: {e}") 