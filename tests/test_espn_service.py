import pytest
from datetime import datetime
import pytz
from unittest.mock import patch, Mock
import requests
from src.services.espn_service import ESPNService
from unittest.mock import ANY

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
    assert espn_service.base_url == "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/2025/segments/0/leagues/484910394"

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
    
    # Проверяем параметры запроса
    call_args = mock_request.call_args
    assert call_args.kwargs['method'] == 'GET'
    assert call_args.kwargs['url'] == espn_service.base_url
    assert call_args.kwargs['params'] == {'view': 'mRoster'}
    assert 'x-fantasy-filter' in call_args.kwargs['headers']

@patch('requests.request')
def test_get_weekly_stats(mock_request, espn_service, mock_response):
    mock_request.return_value = mock_response
    
    # Тест с конкретной датой начала недели (7 октября 2024, 12:00)
    test_date = datetime(2024, 10, 7, 12, 0, tzinfo=pytz.timezone('America/New_York'))
    result = espn_service.get_weekly_stats(test_date)
    
    assert result is not None
    assert "players" in result
    assert len(result["players"]) > 0
    
    # Проверяем параметры запроса
    mock_request.assert_called_once()
    args, kwargs = mock_request.call_args
    assert kwargs['params']['startDate'] == '20241007'
    assert kwargs['params']['endDate'] == '20241013'
    assert kwargs['params']['view'] == 'mStats,kona_player_info'

@patch('requests.request')
def test_error_handling(mock_request, espn_service):
    # Симулируем ошибку сети
    mock_request.side_effect = requests.RequestException("Network error")

    test_date = datetime(2024, 10, 5, 12, 0, tzinfo=pytz.timezone('America/New_York'))
    result = espn_service.get_daily_stats(test_date)
    assert result is None  # При ошибке должен возвращаться None

def test_get_scoring_period_id(espn_service):
    # Тестируем дату в середине сезона 2024-25 (5 октября 2024, 12:00)
    test_date = datetime(2024, 10, 5, 12, 0, tzinfo=pytz.timezone('America/New_York'))
    period_id, season = espn_service._get_scoring_period_id(test_date)
    
    # 4 октября 2024 - начало сезона, 5 октября - 2-й день
    assert period_id == 2
    assert season == 2025

def test_get_week_start_date(espn_service):
    with patch('src.services.espn_service.datetime') as mock_datetime:
        # Устанавливаем среду как текущий день
        mock_date = datetime(2024, 10, 9, 12, 0, tzinfo=pytz.timezone('America/New_York'))
        mock_datetime.now.return_value = mock_date
        
        start_date = espn_service._get_week_start_date()
        
        # Проверяем, что получили понедельник той же недели
        assert start_date.weekday() == 0  # Понедельник
        assert start_date.day == 7  # 7 октября 2024 - понедельник

def test_get_players_by_position(espn_service):
    # Мокаем данные игроков
    espn_service.players_data = [
        {'id': '1', 'name': 'Player 1', 'position': 'RW'},
        {'id': '2', 'name': 'Player 2', 'position': 'C'},
        {'id': '3', 'name': 'Player 3', 'position': 'RW'}
    ]
    
    players = espn_service.get_players_by_position('RW')
    assert len(players) == 2
    for player in players:
        assert player['position'] == 'RW'
        assert 'name' in player

def test_create_player_collage(espn_service):
    players = [
        {'name': 'Test Player', 'position': 'RW'},
        {'name': 'Test Player 2', 'position': 'RW'},
        {'name': 'Test Player 3', 'position': 'RW'}
    ]
    
    collage = espn_service.create_player_collage(players)
    assert collage is not None