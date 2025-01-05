import pytest
from datetime import datetime
import os
from src.services.team_service import TeamService
from src.config import settings
from .fixtures.test_data import (
    SEASON_START,
    TEST_PLAYERS,
    TEST_TEAM_OF_DAY
)

@pytest.fixture
def team_service():
    return TeamService()

def test_team_service_initialization(team_service):
    """Тест инициализации сервиса"""
    assert team_service.stats_service is not None
    assert team_service.image_service is not None

def test_group_players_by_position(team_service):
    """Тест группировки игроков по позициям"""
    grouped = team_service._group_players_by_position(TEST_PLAYERS)
    
    # Проверяем наличие всех позиций
    assert all(pos in grouped for pos in settings.PLAYER_POSITIONS.values())
    
    # Проверяем правильность группировки
    assert len(grouped["C"]) == 1
    assert len(grouped["LW"]) == 1
    assert len(grouped["RW"]) == 1
    assert len(grouped["D"]) == 2
    assert len(grouped["G"]) == 1
    
    # Проверяем содержимое групп
    assert grouped["C"][0]["info"]["primary_position"] == 1
    assert grouped["LW"][0]["info"]["primary_position"] == 2
    assert grouped["RW"][0]["info"]["primary_position"] == 3
    assert all(p["info"]["primary_position"] == 4 for p in grouped["D"])
    assert grouped["G"][0]["info"]["primary_position"] == 5

def test_select_best_players(team_service):
    """Тест выбора лучших игроков"""
    grouped_players = team_service._group_players_by_position(TEST_PLAYERS)
    selected = team_service._select_best_players(grouped_players)
    
    # Проверяем количество игроков
    assert len(selected) == sum(settings.TEAM_OF_DAY_COMPOSITION.values())
    
    # Проверяем состав команды
    positions = [p["position"] for p in selected.values()]
    assert positions.count("C") == settings.TEAM_OF_DAY_COMPOSITION["C"]
    assert positions.count("LW") == settings.TEAM_OF_DAY_COMPOSITION["LW"]
    assert positions.count("RW") == settings.TEAM_OF_DAY_COMPOSITION["RW"]
    assert positions.count("D") == settings.TEAM_OF_DAY_COMPOSITION["D"]
    assert positions.count("G") == settings.TEAM_OF_DAY_COMPOSITION["G"]
    
    # Проверяем что выбраны лучшие игроки
    center = next(p for p in selected.values() if p["position"] == "C")
    assert center["stats"]["total_points"] == 10.5  # Лучший центр из тестовых данных

@pytest.mark.vcr()
def test_get_team_of_day(team_service, mocker):
    """Тест получения команды дня"""
    # Мокаем метод получения статистики
    mocker.patch.object(
        team_service.stats_service,
        'get_daily_stats',
        return_value={"players": TEST_PLAYERS}
    )
    
    team = team_service.get_team_of_day(SEASON_START)
    assert team is not None
    assert team["date"] == SEASON_START.strftime("%Y-%m-%d")
    assert len(team["players"]) == sum(settings.TEAM_OF_DAY_COMPOSITION.values())
    
    # Проверяем общие очки
    total_points = sum(p["stats"]["total_points"] for p in team["players"].values())
    assert team["total_points"] == total_points

@pytest.mark.vcr()
def test_create_team_collage(team_service, mocker):
    """Тест создания коллажа"""
    # Мокаем метод получения фото
    mocker.patch.object(
        team_service.image_service,
        'get_player_photo',
        return_value=os.path.join(settings.CACHE_DIR, "test_photo.png")
    )
    
    # Создаем тестовое фото
    test_photo_dir = os.path.join(settings.CACHE_DIR, "player_images")
    os.makedirs(test_photo_dir, exist_ok=True)
    test_photo_path = os.path.join(test_photo_dir, "test_photo.png")
    
    with open(test_photo_path, 'wb') as f:
        f.write(b'test')
        
    # Тестируем создание коллажа
    collage_path = team_service.create_team_collage(TEST_TEAM_OF_DAY)
    assert collage_path is not None
    assert os.path.exists(collage_path)
    
    # Очищаем после теста
    os.remove(test_photo_path)
    if os.path.exists(collage_path):
        os.remove(collage_path) 