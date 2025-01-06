"""
Тесты для сервиса кэширования
"""

import pytest
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from src.services.cache_service import CacheService
import time

@pytest.fixture
def cache_dir(tmp_path):
    """Фикстура для временной директории кэша"""
    return tmp_path / "test_cache"

@pytest.fixture
def cache_service(cache_dir):
    """Фикстура для сервиса кэширования"""
    return CacheService(str(cache_dir))

def test_cache_creation(cache_dir, cache_service):
    """Тест создания директории кэша"""
    assert cache_dir.exists()
    assert cache_dir.is_dir()

def test_cache_data(cache_service):
    """Тест сохранения и получения данных из кэша"""
    test_data = {"test": "data"}
    cache_service.cache_data("test_key", test_data)
    
    cached = cache_service.get_cached_data("test_key")
    assert cached == test_data

def test_cache_expiration(cache_service, monkeypatch):
    """Тест устаревания кэша"""
    test_data = {"test": "data"}
    cache_service.cache_data("test_key", test_data)
    
    # Создаем мок для time.time()
    current_time = time.time()
    future_time = current_time + 3601  # 1 час + 1 секунда
    
    def mock_time():
        return future_time
    
    monkeypatch.setattr(time, 'time', mock_time)
    
    cached = cache_service.get_cached_data("test_key", max_age=3600)
    assert cached is None

def test_clear_cache(cache_service):
    """Тест очистки кэша"""
    test_data = {"test": "data"}
    cache_service.cache_data("test_key1", test_data)
    cache_service.cache_data("test_key2", test_data)
    
    # Очистка конкретного ключа
    cache_service.clear_cache("test_key1")
    assert cache_service.get_cached_data("test_key1") is None
    assert cache_service.get_cached_data("test_key2") is not None
    
    # Полная очистка
    cache_service.clear_cache()
    assert cache_service.get_cached_data("test_key2") is None

def test_invalid_json(cache_service, cache_dir):
    """Тест обработки некорректного JSON"""
    # Создаем файл с некорректным JSON
    bad_json_file = cache_dir / "bad_key.json"
    bad_json_file.write_text("{invalid json")
    
    assert cache_service.get_cached_data("bad_key") is None 