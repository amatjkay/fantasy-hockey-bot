import pytest
from datetime import datetime, timedelta
import json
import os
from src.services.stats_service import StatsService

@pytest.fixture
def stats_service():
    return StatsService()

@pytest.fixture
def sample_date():
    return datetime(2024, 10, 4)

@pytest.fixture
def sample_team():
    return {
        "C": {
            "info": {
                "id": "1234",
                "name": "Test Player",
                "primary_position": 1
            },
            "stats": {
                "total_points": 10.5
            }
        }
    }

def test_update_player_stats_basic(stats_service, sample_team, sample_date, tmp_path):
    """Тест базового обновления статистики игрока"""
    # Создаем тестовый файл статистики
    stats_file = tmp_path / "stats.json"
    with open(stats_file, "w") as f:
        json.dump({"days": {}, "players": {}}, f)
        
    # Обновляем статистику
    stats_service.update_player_stats(sample_team, sample_date)
    
    # Проверяем результаты
    with open(stats_file, "r") as f:
        stats = json.load(f)
        
    date_str = sample_date.strftime("%Y-%m-%d")
    player_id = sample_team["C"]["info"]["id"]
    
    # Проверяем, что статистика за день добавлена
    assert date_str in stats["days"]
    assert stats["days"][date_str] == sample_team
    
    # Проверяем, что статистика игрока обновлена
    assert player_id in stats["players"]
    assert stats["players"][player_id]["info"] == sample_team["C"]["info"]
    assert date_str in stats["players"][player_id]["appearances"]
    assert stats["players"][player_id]["total_points"] == sample_team["C"]["stats"]["total_points"]

def test_update_player_stats_multiple_days(stats_service, sample_team, sample_date, tmp_path):
    """Тест обновления статистики за несколько дней"""
    # Создаем тестовый файл статистики
    stats_file = tmp_path / "stats.json"
    with open(stats_file, "w") as f:
        json.dump({"days": {}, "players": {}}, f)
        
    # Обновляем статистику за два дня
    stats_service.update_player_stats(sample_team, sample_date)
    stats_service.update_player_stats(sample_team, sample_date + timedelta(days=1))
    
    # Проверяем результаты
    with open(stats_file, "r") as f:
        stats = json.load(f)
        
    date_str_1 = sample_date.strftime("%Y-%m-%d")
    date_str_2 = (sample_date + timedelta(days=1)).strftime("%Y-%m-%d")
    player_id = sample_team["C"]["info"]["id"]
    
    # Проверяем статистику за оба дня
    assert date_str_1 in stats["days"]
    assert date_str_2 in stats["days"]
    assert len(stats["players"][player_id]["appearances"]) == 2
    assert stats["players"][player_id]["total_points"] == sample_team["C"]["stats"]["total_points"] * 2 