import pytest
from datetime import datetime
import pytz
import os
from src.services.stats_service import StatsService
from src.config.settings import ESPN_API, ESPN_TIMEZONE, load_env_vars

@pytest.fixture(scope="session", autouse=True)
def check_env_vars():
    """Проверяем наличие необходимых переменных окружения перед запуском тестов"""
    try:
        load_env_vars()
    except ValueError as e:
        pytest.skip(str(e))

@pytest.fixture
def stats_service():
    return StatsService()

def test_espn_api_connection(stats_service):
    """Проверяем базовое подключение к API ESPN"""
    url = f"https://fantasy.espn.com/apis/v3/games/fhl/seasons/{ESPN_API['season_id']}/segments/0/leagues/{ESPN_API['league_id']}"
    params = {
        'view': ['mScoreboard', 'mRoster', 'mTeam']
    }
    response = stats_service._make_request(url, params)
    assert response is not None, "API должно возвращать данные"
    assert isinstance(response, dict), "Ответ должен быть словарем"

def test_request_headers(stats_service):
    """Проверяем корректность заголовков запроса"""
    headers = stats_service.headers
    assert 'User-Agent' in headers, "Отсутствует заголовок User-Agent"
    assert 'Accept' in headers, "Отсутствует заголовок Accept"
    assert 'Content-Type' in headers, "Отсутствует заголовок Content-Type"
    assert headers['Content-Type'] == 'application/json', "Неверный Content-Type"

def test_daily_stats_collection(stats_service):
    """Проверяем сбор ежедневной статистики"""
    date = datetime.now(ESPN_TIMEZONE)
    stats = stats_service.collect_stats(date)
    assert stats is not None, "Ежедневная статистика должна быть получена"
    assert isinstance(stats, dict), "Статистика должна быть словарем"
    assert 'scoreboard' in stats, "В статистике должен быть раздел scoreboard"
    assert 'players' in stats, "В статистике должен быть раздел players"
    assert 'date' in stats, "В статистике должна быть дата"

def test_weekly_stats_collection(stats_service):
    """Проверяем сбор еженедельной статистики"""
    start_date = datetime.now(ESPN_TIMEZONE)
    stats = stats_service.collect_weekly_stats(start_date)
    assert stats is not None, "Еженедельная статистика должна быть получена"
    assert isinstance(stats, dict), "Статистика должна быть словарем"
    assert len(stats) > 0, "Статистика должна содержать данные хотя бы за один день"

def test_error_handling(stats_service):
    """Проверяем обработку ошибок при неверном URL"""
    url = "https://fantasy.espn.com/invalid/url"
    response = stats_service._make_request(url)
    assert response is None, "Должен быть возвращен None при ошибке"

def test_authentication_headers(stats_service):
    """Проверяем наличие аутентификационных заголовков"""
    cookies = stats_service.cookies
    assert 'swid' in cookies, "Отсутствует cookie SWID"
    assert 'espn_s2' in cookies, "Отсутствует cookie ESPN_S2"
    assert cookies['swid'].startswith('{') and cookies['swid'].endswith('}'), "Неверный формат SWID"
    assert len(cookies['espn_s2']) > 0, "Пустой ESPN_S2"

def test_league_access(stats_service):
    """Проверяем доступ к лиге"""
    url = f"https://fantasy.espn.com/apis/v3/games/fhl/seasons/{ESPN_API['season_id']}/segments/0/leagues/{ESPN_API['league_id']}"
    params = {
        'view': ['mScoreboard', 'mRoster', 'mTeam']
    }
    response = stats_service._make_request(url, params)
    assert response is not None, "Нет доступа к лиге"
    assert isinstance(response, dict), "Ответ должен быть словарем"
    assert 'gameId' in response or 'id' in response, "Ответ должен содержать ID игры или лиги" 