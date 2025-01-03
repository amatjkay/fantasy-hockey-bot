import pytest
import requests
import pytz
from datetime import datetime
from unittest.mock import patch, Mock

from src.services.espn_service import ESPNService

@pytest.fixture
def espn_service():
    return ESPNService()

@pytest.fixture
def mock_response():
    mock = Mock()
    mock.status_code = 200
    return mock

def test_espn_service_initialization(espn_service):
    assert espn_service is not None
    assert espn_service.base_url is not None
    assert espn_service.headers is not None

@patch('requests.request')
def test_get_daily_stats(mock_request, espn_service, mock_response):
    mock_request.return_value = mock_response
    mock_response.json.return_value = {
        "players": [
            {
                "id": 4233563,
                "fullName": "Test Player",
                "defaultPositionId": 1,
                "stats": [{"points": 10.5, "totalPoints": 10.5}]
            }
        ]
    }
    mock_response.status_code = 200

    # Тест с конкретной датой (5 октября 2024, 12:00)
    test_date = datetime(2024, 10, 5, 12, 0, tzinfo=pytz.timezone('America/New_York'))
    result = espn_service.get_daily_stats(test_date)

    assert result is not None
    assert "players" in result
    assert len(result["players"]) > 0
    assert isinstance(result["players"][0]["id"], int)

    # Проверяем, что запрос был сделан
    assert mock_request.call_count == 1

@patch('requests.request')
def test_get_weekly_stats(mock_request, espn_service, mock_response):
    mock_request.return_value = mock_response
    mock_response.json.return_value = {
        "players": [
            {
                "id": 4233563,
                "fullName": "Test Player",
                "defaultPositionId": 1,
                "stats": [{"points": 10.5, "totalPoints": 10.5}]
            }
        ]
    }

    # Тест с конкретной датой начала недели (7 октября 2024, 12:00)
    test_date = datetime(2024, 10, 7, 12, 0, tzinfo=pytz.timezone('America/New_York'))
    result = espn_service.get_weekly_stats(test_date)

    assert result is not None
    assert "players" in result
    assert len(result["players"]) > 0
    assert isinstance(result["players"][0]["id"], int)

@patch('requests.request')
def test_error_handling(mock_request, espn_service):
    # Симулируем ошибку сети
    mock_request.side_effect = requests.RequestException("Network error")

    test_date = datetime(2024, 10, 5, 12, 0, tzinfo=pytz.timezone('America/New_York'))
    result = espn_service.get_daily_stats(test_date)
    assert result is None  # При ошибке должен возвращаться None

def test_get_scoring_period_id(espn_service):
    # Тест с конкретной датой (5 октября 2024, 12:00)
    test_date = datetime(2024, 10, 5, 12, 0, tzinfo=pytz.timezone('America/New_York'))
    period_id = espn_service.get_scoring_period_id(test_date)
    assert isinstance(period_id, int)
    assert period_id > 0

def test_get_week_start_date(espn_service):
    # Тест с конкретной датой (5 октября 2024, 12:00)
    test_date = datetime(2024, 10, 5, 12, 0, tzinfo=pytz.timezone('America/New_York'))
    start_date = espn_service.get_week_start_date(test_date)
    assert isinstance(start_date, datetime)
    assert start_date.weekday() == 0  # Должен быть понедельник

def test_get_players_by_position(espn_service):
    players = [
        {"defaultPositionId": 1, "fullName": "Player 1"},
        {"defaultPositionId": 2, "fullName": "Player 2"},
        {"defaultPositionId": 3, "fullName": "Player 3"},
        {"defaultPositionId": 4, "fullName": "Player 4"},
        {"defaultPositionId": 5, "fullName": "Player 5"}
    ]

    result = espn_service.get_players_by_position(players)
    assert isinstance(result, dict)
    assert all(pos in result for pos in ['C', 'LW', 'RW', 'D', 'G'])