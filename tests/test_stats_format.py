import pytest
import json
import pytz
from datetime import datetime
from src.services.stats_service import StatsService

@pytest.fixture
def stats_service():
    return StatsService()

def test_stats_file_structure(stats_service, tmp_path):
    """Тест структуры файла статистики"""
    stats_file = tmp_path / "stats.json"
    
    # Создаем минимальный набор данных
    test_data = {
        "days": {},
        "players": {},
        "weekly_grades": {},
        "daily_appearances": {}
    }
    
    with open(stats_file, "w") as f:
        json.dump(test_data, f)
    
    # Обновляем статистику
    date = datetime(2024, 10, 7, tzinfo=pytz.UTC)
    player_data = [{
        "id": "1",
        "fullName": "Test Player",
        "defaultPositionId": 1,
        "stats": [{"points": 10}]
    }]
    
    stats_service.update_player_stats(player_data, date, str(stats_file))
    
    # Проверяем структуру файла
    with open(stats_file) as f:
        stats = json.load(f)
    
    # Проверяем основные секции
    assert "days" in stats
    assert "players" in stats
    assert "weekly_grades" in stats
    assert "daily_appearances" in stats
    
    # Проверяем формат дат
    day_key = date.strftime('%Y-%m-%d')
    assert day_key in stats["days"]
    
    # Проверяем структуру данных игрока
    player = stats["players"]["1"]
    assert isinstance(player["name"], str)
    assert isinstance(player["total_points"], (int, float))
    assert player["grade"] in ["common", "uncommon", "rare", "epic", "legend"]
    assert isinstance(player["weekly_appearances"], int)
    assert isinstance(player["appearances"], dict)
    
    # Проверяем структуру дневной статистики
    day_stats = stats["days"][day_key]
    for position in ["C", "LW", "RW", "D", "G"]:
        assert position in day_stats
        assert isinstance(day_stats[position], list)
        if day_stats[position]:
            player_stat = day_stats[position][0]
            assert "id" in player_stat
            assert "name" in player_stat
            assert "points" in player_stat
            assert "grade" in player_stat

def test_stats_data_types(stats_service, tmp_path):
    """Тест типов данных в статистике"""
    stats_file = tmp_path / "stats.json"
    date = datetime(2024, 10, 7, tzinfo=pytz.UTC)
    
    # Создаем тестовые данные с разными типами
    player_data = [{
        "id": "1",
        "fullName": "Test Player",
        "defaultPositionId": 1,
        "stats": [{"points": 10.5}]  # Дробные очки
    }]
    
    stats_service.update_player_stats(player_data, date, str(stats_file))
    
    with open(stats_file) as f:
        stats = json.load(f)
    
    player = stats["players"]["1"]
    assert isinstance(player["total_points"], float)  # Проверяем, что дробные очки сохраняются корректно
    
    day_key = date.strftime('%Y-%m-%d')
    assert isinstance(stats["daily_appearances"][day_key], list)  # Проверяем, что set конвертируется в list для JSON

def test_timezone_handling(stats_service, tmp_path):
    """Тест обработки временных зон"""
    stats_file = tmp_path / "stats.json"
    
    # Тестируем разные форматы дат
    dates = [
        datetime(2024, 10, 7),  # Без временной зоны
        datetime(2024, 10, 7, tzinfo=pytz.UTC),  # UTC
        datetime(2024, 10, 7, tzinfo=pytz.timezone('US/Eastern'))  # EST
    ]
    
    player_data = [{
        "id": "1",
        "fullName": "Test Player",
        "defaultPositionId": 1,
        "stats": [{"points": 10}]
    }]
    
    for date in dates:
        stats_service.update_player_stats(player_data, date, str(stats_file))
        
        with open(stats_file) as f:
            stats = json.load(f)
        
        # Проверяем, что все даты сохранены в одном формате
        day_key = date.strftime('%Y-%m-%d')
        assert day_key in stats["days"]

def test_missing_data_handling(stats_service, tmp_path):
    """Тест обработки отсутствующих данных"""
    stats_file = tmp_path / "stats.json"
    date = datetime(2024, 10, 7, tzinfo=pytz.UTC)
    
    # Тестируем неполные данные игрока
    incomplete_player_data = [{
        "id": "1",
        "fullName": "Test Player",
        "defaultPositionId": 1,
        "stats": []  # Пустая статистика
    }]
    
    stats_service.update_player_stats(incomplete_player_data, date, str(stats_file))
    
    with open(stats_file) as f:
        stats = json.load(f)
    
    # Проверяем, что структура файла создана
    assert "days" in stats
    assert "players" in stats
    assert "weekly_grades" in stats
    assert "daily_appearances" in stats
    
    # Проверяем, что игрок без очков не добавлен в статистику
    assert len(stats["players"]) == 0
    
    # Проверяем, что день создан, но пуст
    day_key = date.strftime('%Y-%m-%d')
    assert day_key in stats["days"]
    assert all(len(stats["days"][day_key][pos]) == 0 for pos in ["C", "LW", "RW", "D", "G"])
    
    # Проверяем обработку игрока с нулевыми очками
    player_data = [{
        "id": "1",
        "fullName": "Test Player",
        "defaultPositionId": 1,
        "stats": [{"points": 0}]  # Явно указываем нулевые очки
    }]
    
    stats_service.update_player_stats(player_data, date, str(stats_file))
    
    with open(stats_file) as f:
        stats = json.load(f)
    
    # Проверяем, что игрок с нулевыми очками также не добавлен
    assert len(stats["players"]) == 0
    assert all(len(stats["days"][day_key][pos]) == 0 for pos in ["C", "LW", "RW", "D", "G"]) 