import pytest
from datetime import datetime
import pytz
from unittest.mock import patch, Mock
import requests
from src.services.espn_service import ESPNService

@pytest.fixture
def espn_service():
    return ESPNService()

@pytest.fixture
def mock_response():
    mock = Mock()
    mock.json.return_value = {
        "players": [
            {
                "id": "12345",
                "fullName": "Test Player",
                "stats": [{"points": 10}]
            }
        ]
    }
    mock.status_code = 200
    return mock

def test_espn_service_initialization(espn_service):
    assert espn_service is not None
    assert espn_service.base_url == "https://fantasy.espn.com/apis/v3/games/nhl/seasons"
    assert espn_service.season == datetime.now().year
    assert espn_service.season_start_day == 4
    assert espn_service.season_start_month == 10

@patch('requests.get')
def test_get_daily_stats(mock_get, espn_service, mock_response):
    mock_get.return_value = mock_response
    
    # Тест с конкретной датой
    test_date = datetime(2024, 1, 1, tzinfo=pytz.timezone('America/New_York'))
    result = espn_service.get_daily_stats(test_date)
    
    assert result is not None
    assert "players" in result
    assert len(result["players"]) > 0
    assert result["players"][0]["id"] == "12345"
    
    # Проверяем параметры запроса
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert 'scoringPeriodId' in kwargs['params']

@patch('requests.get')
def test_get_weekly_stats(mock_get, espn_service, mock_response):
    mock_get.return_value = mock_response
    
    # Тест с конкретной датой начала недели
    test_date = datetime(2024, 1, 1, tzinfo=pytz.timezone('America/New_York'))
    result = espn_service.get_weekly_stats(test_date)
    
    assert result is not None
    assert "players" in result
    assert len(result["players"]) > 0
    
    # Проверяем параметры запроса
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert 'startDate' in kwargs['params']
    assert 'endDate' in kwargs['params']

@patch('requests.get')
def test_error_handling(mock_get, espn_service):
    # Симулируем ошибку сети
    mock_get.side_effect = requests.RequestException("Network error")
    
    result = espn_service.get_daily_stats()
    assert result is None
    
    result = espn_service.get_weekly_stats()
    assert result is None

def test_get_scoring_period_id(espn_service):
    # Тестируем дату в середине сезона 2023-24
    test_date = datetime(2024, 1, 1)
    period_id = espn_service._get_scoring_period_id(test_date)
    
    # 4 октября 2024 - начало сезона, 1 января 2025 - 90-й день
    assert period_id == 90

def test_get_week_start_date(espn_service):
    with patch('src.services.espn_service.datetime') as mock_datetime:
        # Устанавливаем среду как текущий день
        mock_date = datetime(2025, 1, 1, tzinfo=pytz.timezone('America/New_York'))
        mock_datetime.now.return_value = mock_date
        
        start_date = espn_service._get_week_start_date()
        
        # Проверяем, что получили понедельник той же недели
        assert start_date.weekday() == 0  # Понедельник
        assert start_date.day == 30  # 30 декабря 2024 - понедельник

def test_get_players_by_position():
    service = ESPNService()
    players = service.get_players_by_position('RW')
    
    assert len(players) > 0
    for player in players:
        assert player['position'] == 'RW'
        assert 'name' in player
        # Убираем проверку fantasy_points
        assert 'fantasy_points' not in player

def test_create_player_collage():
    service = ESPNService()
    players = [
        {'name': 'Test Player', 'position': 'RW'},
        {'name': 'Test Player 2', 'position': 'RW'},
        {'name': 'Test Player 3', 'position': 'RW'}
    ]
    
    collage = service.create_player_collage(players)
    assert collage is not None