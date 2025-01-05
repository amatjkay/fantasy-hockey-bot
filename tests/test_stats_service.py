import pytest
from datetime import datetime, timedelta
import os
import requests
from src.services.stats_service import StatsService
from src.config import settings
from .fixtures.test_data import (
    SEASON_START,
    SEASON_END,
    INVALID_DATE,
    TEST_PLAYERS
)

@pytest.fixture
def stats_service():
    return StatsService()

def test_stats_service_initialization(stats_service):
    """Тест инициализации сервиса"""
    assert stats_service.session is not None
    assert stats_service.base_url == settings.ESPN_API['BASE_URL']

def test_scoring_period_id_calculation(stats_service):
    """Тест расчета scoring_period_id"""
    # Тест начала сезона
    assert stats_service._get_scoring_period_id(SEASON_START) == settings.SEASON_START_SCORING_PERIOD
    
    # Тест для даты до начала сезона
    assert stats_service._get_scoring_period_id(INVALID_DATE) is None
    
    # Тест для произвольной даты в сезоне
    test_date = SEASON_START + timedelta(days=10)
    expected_id = settings.SEASON_START_SCORING_PERIOD + 10
    assert stats_service._get_scoring_period_id(test_date) == expected_id

@pytest.mark.vcr()
def test_get_daily_stats(stats_service, mocker):
    """Тест получения статистики за день"""
    # Мокаем ответ от API
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"players": []}
    mock_response.status_code = 200
    mocker.patch.object(stats_service.session, 'get', return_value=mock_response)
    
    stats = stats_service.get_daily_stats(SEASON_START)
    assert stats is not None
    assert "date" in stats
    assert "players" in stats
    assert isinstance(stats["players"], dict)

def test_fantasy_filter_building(stats_service):
    """Тест построения фильтра для API"""
    # Тест без scoring_period_id
    basic_filter = eval(stats_service._build_fantasy_filter())
    assert "players" in basic_filter
    assert "filterSlotIds" in basic_filter["players"]
    assert "sortPercOwned" in basic_filter["players"]
    
    # Тест с scoring_period_id
    period_filter = eval(stats_service._build_fantasy_filter(94))
    assert "filterStatsForCurrentSeasonScoringPeriodId" in period_filter["players"]
    assert "filterRanksForScoringPeriodIds" in period_filter["players"]
    assert period_filter["players"]["filterStatsForCurrentSeasonScoringPeriodId"]["value"] == [94]

def test_auth_headers(stats_service):
    """Тест формирования заголовков авторизации"""
    headers = stats_service._get_auth_headers()
    
    assert "Cookie" in headers
    assert f"SWID={settings.ESPN_API['swid']}" in headers["Cookie"]
    assert f"espn_s2={settings.ESPN_API['s2']}" in headers["Cookie"]
    assert headers["x-fantasy-source"] == "kona"
    assert "x-fantasy-filter" in headers

@pytest.mark.vcr()
def test_invalid_date_handling(stats_service):
    """Тест обработки невалидной даты"""
    stats = stats_service.get_daily_stats(INVALID_DATE)
    assert stats is None

@pytest.mark.vcr()
def test_stats_processing(stats_service, mocker):
    """Тест обработки статистики"""
    # Мокаем ответ от API
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "players": [
            {
                "id": "123456",
                "firstName": "Test",
                "lastName": "Player",
                "defaultPositionId": 1,
                "proTeamId": 1,
                "stats": [
                    {
                        "scoringPeriodId": settings.SEASON_START_SCORING_PERIOD,
                        "stats": {
                            "6": 1,  # goals
                            "7": 2,  # assists
                            "13": 3,  # shots
                            "31": 0,  # saves
                            "32": 0   # goals against
                        },
                        "appliedTotal": 10.5
                    }
                ]
            }
        ]
    }
    mock_response.status_code = 200
    mocker.patch.object(stats_service.session, 'get', return_value=mock_response)
    mocker.patch.object(stats_service, '_get_current_scoring_period', return_value=settings.SEASON_START_SCORING_PERIOD)
    
    stats = stats_service.get_daily_stats(SEASON_START)
    assert stats is not None
    assert "123456" in stats["players"]
    assert stats["players"]["123456"]["stats"]["total_points"] == 10.5

@pytest.mark.vcr()
def test_retry_mechanism(stats_service, mocker):
    """Тест механизма повторных попыток"""
    # Мокаем неудачные попытки
    mock_response_fail = mocker.Mock()
    mock_response_fail.raise_for_status.side_effect = requests.exceptions.RequestException("Test error")
    mock_response_fail.status_code = 500
    
    mock_response_success = mocker.Mock()
    mock_response_success.json.return_value = {"players": []}
    mock_response_success.status_code = 200
    mock_response_success.raise_for_status = lambda: None
    
    # Мокаем метод get с двумя неудачными попытками и одной успешной
    mock_get = mocker.patch.object(
        stats_service.session,
        'get',
        side_effect=[mock_response_fail, mock_response_fail, mock_response_success]
    )
    
    # Мокаем _get_current_scoring_period для стабильности теста
    mocker.patch.object(
        stats_service,
        '_get_current_scoring_period',
        return_value=settings.SEASON_START_SCORING_PERIOD
    )
    
    stats = stats_service.get_daily_stats(SEASON_START)
    assert stats is not None
    assert mock_get.call_count == 3  # Две неудачные попытки и одна успешная

def test_response_validation(stats_service):
    """Тест валидации ответа от API"""
    # Тест корректного ответа
    valid_response = {"players": []}
    assert stats_service._validate_response(valid_response) is True
    
    # Тест некорректного ответа
    invalid_response = {"teams": []}
    assert stats_service._validate_response(invalid_response) is False
    
    # Тест пустого ответа
    assert stats_service._validate_response({}) is False 