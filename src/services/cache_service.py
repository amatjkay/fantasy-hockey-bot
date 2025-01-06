"""
Сервис для кэширования данных API
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import json
import os
import logging
from pathlib import Path
import time

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self, cache_dir: str = "cache"):
        """
        Инициализация сервиса кэширования
        
        Args:
            cache_dir: Директория для хранения кэша
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def get_cached_data(self, key: str, max_age: int = 3600) -> Optional[Dict]:
        """
        Получение данных из кэша
        
        Args:
            key: Ключ кэша
            max_age: Максимальный возраст кэша в секундах
            
        Returns:
            Dict если данные найдены и актуальны, иначе None
        """
        cache_file = self.cache_dir / f"{key}.json"
        
        if not cache_file.exists():
            return None
            
        # Проверяем возраст файла
        file_age = time.time() - cache_file.stat().st_mtime
        if file_age > max_age:
            logger.debug(f"Кэш устарел для {key}")
            return None
            
        try:
            with cache_file.open('r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка чтения кэша {key}: {e}")
            return None
            
    def cache_data(self, key: str, data: Dict) -> None:
        """
        Сохранение данных в кэш
        
        Args:
            key: Ключ кэша
            data: Данные для сохранения
        """
        cache_file = self.cache_dir / f"{key}.json"
        
        try:
            with cache_file.open('w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Данные сохранены в кэш: {key}")
        except Exception as e:
            logger.error(f"Ошибка сохранения в кэш {key}: {e}")
            
    def clear_cache(self, key: Optional[str] = None) -> None:
        """
        Очистка кэша
        
        Args:
            key: Если указан, удаляется только этот ключ
        """
        if key:
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()
                logger.debug(f"Удален кэш: {key}")
        else:
            for file in self.cache_dir.glob("*.json"):
                file.unlink()
            logger.debug("Кэш полностью очищен") 