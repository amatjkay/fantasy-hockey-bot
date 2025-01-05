import pytest
from datetime import datetime
import os
from src.services.stats_service import StatsService
from src.services.team_service import TeamService
from src.config import settings

@pytest.fixture
def stats_service():
    return StatsService()

@pytest.fixture
def team_service():
    return TeamService()

def test_stats_service_initialization(stats_service):
    assert stats_service.session is not None
    assert stats_service.base_url == settings.ESPN_API['BASE_URL']

def test_scoring_period_id_calculation(stats_service):
    """Тест расчета scoring_period_id"""
    # Тест начала сезона
    start_date = datetime.strptime(settings.SEASON_START, '%Y-%m-%d')
    assert stats_service._get_scoring_period_id(start_date) == settings.SEASON_START_SCORING_PERIOD
    
    # Тест для даты до начала сезона
    invalid_date = datetime(2024, 10, 3)
    assert stats_service._get_scoring_period_id(invalid_date) is None
    
    # Тест для произвольной даты в сезоне
    test_date = datetime(2024, 10, 14)  # 10 дней после начала
    expected_id = settings.SEASON_START_SCORING_PERIOD + 10
    assert stats_service._get_scoring_period_id(test_date) == expected_id

@pytest.mark.vcr()
def test_get_daily_stats(stats_service):
    """Тест получения статистики за день"""
    date = datetime(2024, 10, 4)  # Первый день сезона
    stats = stats_service.get_daily_stats(date)
    
    assert stats is not None
    assert "date" in stats
    assert "players" in stats
    assert isinstance(stats["players"], dict)

def test_team_composition(team_service):
    """Тест состава команды"""
    date = datetime(2024, 10, 4)
    team = team_service.get_team_of_day(date)
    
    assert team is not None
    assert "date" in team
    assert "players" in team
    assert "total_points" in team
    
    # Проверяем состав команды
    positions = [p["position"] for p in team["players"].values()]
    assert positions.count("C") == settings.TEAM_OF_DAY_COMPOSITION["C"]
    assert positions.count("LW") == settings.TEAM_OF_DAY_COMPOSITION["LW"]
    assert positions.count("RW") == settings.TEAM_OF_DAY_COMPOSITION["RW"]
    assert positions.count("D") == settings.TEAM_OF_DAY_COMPOSITION["D"]
    assert positions.count("G") == settings.TEAM_OF_DAY_COMPOSITION["G"]

def test_player_photo_caching(team_service):
    """Тест кэширования фото игроков"""
    # Создаем тестовое фото
    test_photo_dir = os.path.join(settings.CACHE_DIR, "player_images")
    os.makedirs(test_photo_dir, exist_ok=True)
    
    test_player_id = "test123"
    test_photo_path = os.path.join(test_photo_dir, f"{test_player_id}.png")
    
    # Создаем пустой файл для теста
    with open(test_photo_path, 'wb') as f:
        f.write(b'test')
        
    # Проверяем что фото берется из кэша
    photo_path = team_service.image_service.get_player_photo(test_player_id, "Test Player")
    assert photo_path == test_photo_path
    
    # Очищаем после теста
    os.remove(test_photo_path)

@pytest.mark.vcr()
def test_team_collage_creation(team_service):
    """Тест создания коллажа"""
    date = datetime(2024, 10, 4)
    team = team_service.get_team_of_day(date)
    assert team is not None
    
    collage_path = team_service.create_team_collage(team)
    assert collage_path is not None
    assert os.path.exists(collage_path)
    
    # Проверяем что файл не пустой
    assert os.path.getsize(collage_path) > 0 