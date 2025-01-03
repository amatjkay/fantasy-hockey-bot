import pytest
import pytz
from datetime import datetime
from src.services.stats_service import StatsService

@pytest.fixture
def stats_service():
    return StatsService()

def test_collect_stats(stats_service):
    # Тестируем сбор статистики за конкретный день
    test_date = datetime(2024, 10, 5, tzinfo=pytz.UTC)
    result = stats_service.collect_stats(test_date)
    
    assert result is not None
    assert "players" in result
    assert len(result["players"]) > 0

def test_collect_stats_date_range(stats_service):
    # Тестируем сбор статистики за период
    start_date = datetime(2024, 10, 5, tzinfo=pytz.UTC)
    end_date = datetime(2024, 10, 12, tzinfo=pytz.UTC)
    result = stats_service.collect_stats_range(start_date, end_date)
    
    assert result is not None
    assert "players" in result
    assert len(result["players"]) > 0

def test_collect_stats_invalid_date(stats_service):
    # Тестируем сбор статистики с некорректной датой
    invalid_date = datetime(2023, 1, 1, tzinfo=pytz.UTC)
    
    # Собираем статистику
    result = stats_service.collect_stats(invalid_date)
    
    # Проверяем результаты
    assert result is None 