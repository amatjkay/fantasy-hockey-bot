"""
Тесты для сервиса статистики
"""

import pytest
from datetime import datetime
import json
from unittest.mock import Mock, patch
from src.services.stats_service import StatsService
from src.services.cache_service import CacheService

@pytest.fixture
def mock_response():
    """Фикстура для мока ответа API"""
    mock = Mock()
    mock.json.return_value = {
        "players": [
            {
                "id": "123456",
                "fullName": "Test Player",
                "stats": [{"points": 10}],
                "eligibleSlots": [0, 1, 2]
            }
        ]
    }
    mock.raise_for_status.return_value = None
    return mock

@pytest.fixture
def stats_service():
    """Фикстура для сервиса статистики"""
    return StatsService()

def test_get_daily_stats_cached(stats_service, monkeypatch):
    """Тест получения кэшированных данных"""
    test_date = datetime(2024, 1, 1)
    test_data = {"players": {"123456": {"name": "Test Player"}}}
    
    # Мокаем метод получения данных из кэша
    mock_cache = Mock(spec=CacheService)
    mock_cache.get_cached_data.return_value = test_data
    monkeypatch.setattr(stats_service, 'cache', mock_cache)
    
    result = stats_service.get_daily_stats(test_date)
    
    assert result == test_data
    mock_cache.get_cached_data.assert_called_once()

def test_get_daily_stats_api(stats_service, mock_response, monkeypatch):
    """Тест получения данных через API при отсутствии кэша"""
    test_date = datetime(2024, 1, 1)
    
    # Мокаем кэш и API
    mock_cache = Mock(spec=CacheService)
    mock_cache.get_cached_data.return_value = None
    monkeypatch.setattr(stats_service, 'cache', mock_cache)
    
    mock_session = Mock()
    mock_session.get.return_value = mock_response
    monkeypatch.setattr(stats_service, 'session', mock_session)
    
    # Мокаем получение scoring_period_id
    monkeypatch.setattr(stats_service, '_get_scoring_period_id', lambda x: 1)
    
    result = stats_service.get_daily_stats(test_date)
    
    assert result is not None
    assert "players" in result
    mock_cache.get_cached_data.assert_called_once()
    mock_cache.cache_data.assert_called_once()
    mock_session.get.assert_called_once()

def test_get_daily_stats_api_error(stats_service, monkeypatch):
    """Тест обработки ошибок API"""
    test_date = datetime(2024, 1, 1)
    
    # Мокаем кэш и API с ошибкой
    mock_cache = Mock(spec=CacheService)
    mock_cache.get_cached_data.return_value = None
    monkeypatch.setattr(stats_service, 'cache', mock_cache)
    
    mock_session = Mock()
    mock_session.get.side_effect = Exception("API Error")
    monkeypatch.setattr(stats_service, 'session', mock_session)
    
    # Мокаем получение scoring_period_id
    monkeypatch.setattr(stats_service, '_get_scoring_period_id', lambda x: 1)
    
    result = stats_service.get_daily_stats(test_date)
    
    assert result is None
    mock_cache.get_cached_data.assert_called_once()
    mock_cache.cache_data.assert_not_called()
    mock_session.get.assert_called_once()

def test_fantasy_filter_building(stats_service):
    """Тест построения фильтра для API"""
    filter_str = stats_service._build_fantasy_filter(1)
    filter_data = json.loads(filter_str)
    
    assert "players" in filter_data
    assert "filterSlotIds" in filter_data["players"]
    assert "filterStatsForCurrentSeasonScoringPeriodId" in filter_data["players"]
    assert filter_data["players"]["filterStatsForCurrentSeasonScoringPeriodId"]["value"] == [1]

def test_auth_headers(stats_service):
    """Тест формирования заголовков авторизации"""
    headers = stats_service._get_auth_headers()
    
    assert "Accept" in headers
    assert "Content-Type" in headers
    assert "x-fantasy-filter" in headers

def test_response_validation(stats_service, mock_response):
    """Тест валидации ответа API"""
    valid_data = mock_response.json()
    assert stats_service._validate_response(valid_data) is True
    
    # Тест невалидных данных
    assert stats_service._validate_response({}) is False
    assert stats_service._validate_response({"players": []}) is True
    assert stats_service._validate_response(None) is False

def test_scoring_period_calculation(stats_service):
    """Тест расчета scoring_period_id"""
    test_date = datetime(2024, 10, 4)  # Первый день сезона
    period_id = stats_service._get_scoring_period_id(test_date)
    assert period_id == 1
    
    test_date = datetime(2024, 10, 5)  # Второй день сезона
    period_id = stats_service._get_scoring_period_id(test_date)
    assert period_id == 2 