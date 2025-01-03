import pytest
from datetime import datetime, timedelta
import pytz
from unittest.mock import Mock, patch
from src.services.espn_service import ESPNService
from scripts.collect_initial_stats import collect_stats

@pytest.fixture
def mock_espn_service():
    service = Mock(spec=ESPNService)
    return service

@pytest.fixture
def mock_logger():
    return Mock()

def test_collect_stats_success(mock_espn_service, mock_logger):
    # Подготавливаем тестовые данные
    start_date = datetime(2024, 10, 4, tzinfo=pytz.UTC)
    end_date = start_date + timedelta(days=2)
    
    # Настраиваем поведение мока
    mock_espn_service.get_daily_stats.return_value = {
        'players': [
            {
                'id': '1234',
                'fullName': 'Test Player',
                'stats': [{'points': 10}]
            }
        ]
    }
    mock_espn_service.get_team_of_the_day.return_value = [
        {
            'id': '1234',
            'name': 'Test Player',
            'position': 'C',
            'stats': [{'points': 10}]
        }
    ]
    
    # Вызываем тестируемую функцию
    collect_stats(mock_espn_service, start_date, end_date, mock_logger)
    
    # Проверяем, что функции были вызваны нужное количество раз
    assert mock_espn_service.get_daily_stats.call_count == 3
    assert mock_espn_service.get_team_of_the_day.call_count == 3
    assert mock_logger.info.call_count >= 6

def test_collect_stats_no_data(mock_espn_service, mock_logger):
    # Подготавливаем тестовые данные
    start_date = datetime(2024, 10, 4, tzinfo=pytz.UTC)
    end_date = start_date + timedelta(days=1)
    
    # Настраиваем поведение мока
    mock_espn_service.get_daily_stats.return_value = None
    
    # Вызываем тестируемую функцию
    collect_stats(mock_espn_service, start_date, end_date, mock_logger)
    
    # Проверяем, что функции были вызваны нужное количество раз
    assert mock_espn_service.get_daily_stats.call_count == 6  # 2 дня * 3 попытки
    assert mock_espn_service.get_team_of_the_day.call_count == 0
    assert mock_logger.warning.call_count >= 2

def test_collect_stats_error_handling(mock_espn_service, mock_logger):
    # Подготавливаем тестовые данные
    start_date = datetime(2024, 10, 4, tzinfo=pytz.UTC)
    end_date = start_date + timedelta(days=1)
    
    # Настраиваем поведение мока
    mock_espn_service.get_daily_stats.side_effect = Exception("Test error")
    
    # Вызываем тестируемую функцию
    collect_stats(mock_espn_service, start_date, end_date, mock_logger)
    
    # Проверяем, что ошибки были обработаны
    assert mock_espn_service.get_daily_stats.call_count == 6  # 2 дня * 3 попытки
    assert mock_logger.error.call_count >= 2 