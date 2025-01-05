import pytest
import json
import pytz
from datetime import datetime, timedelta
from src.services.stats_service import StatsService

@pytest.fixture
def stats_service():
    return StatsService()

@pytest.fixture
def sample_team():
    return [
        {
            'id': '1234',
            'fullName': 'Test Player 1',
            'defaultPositionId': 1,
            'stats': [{'points': 10.5, 'totalPoints': 10.5}]
        },
        {
            'id': '5678',
            'fullName': 'Test Player 2',
            'defaultPositionId': 5,
            'stats': [{'points': 8.5, 'savePct': 0.925, 'totalPoints': 8.5}]
        }
    ]

@pytest.fixture
def sample_date():
    return datetime(2024, 10, 7, tzinfo=pytz.UTC)

def test_update_player_stats_new_day(stats_service, sample_team, sample_date, tmp_path):
    # Подготавливаем временный файл для тестов
    stats_file = tmp_path / "player_stats.json"
    with open(stats_file, 'w') as f:
        json.dump({"days": {}, "players": {}, "weekly_grades": {}}, f)

    # Обновляем статистику
    stats_service.update_player_stats(sample_team, sample_date, str(stats_file))

    # Проверяем результаты
    with open(stats_file) as f:
        stats = json.load(f)

    assert "days" in stats
    day_key = "2024-10-07"
    assert day_key in stats["days"]
    
    # Проверяем наличие позиций и игроков
    day_stats = stats["days"][day_key]
    assert "C" in day_stats
    assert "LW" in day_stats
    assert "RW" in day_stats
    assert "D" in day_stats
    assert "G" in day_stats
    
    # Проверяем статистику центрального нападающего
    center = next(p for p in day_stats["C"] if p["id"] == "1234")
    assert center["points"] == 10.5
    assert center["grade"] == "common"  # Первое попадание - остается common

def test_update_player_stats_grade_progression(stats_service, sample_team, sample_date, tmp_path):
    # Подготавливаем временный файл для тестов
    stats_file = tmp_path / "player_stats.json"
    with open(stats_file, 'w') as f:
        json.dump({"days": {}, "players": {}, "weekly_grades": {}}, f)

    # Обновляем статистику за несколько дней в одной неделе
    for i in range(5):  # 5 дней подряд в команде дня
        current_date = sample_date + timedelta(days=i)
        stats_service.update_player_stats(sample_team, current_date, str(stats_file))

    # Проверяем результаты
    with open(stats_file) as f:
        stats = json.load(f)

    # Проверяем прогресс грейда по дням
    for i, grade in enumerate(["common", "uncommon", "rare", "epic", "legend"]):
        day_key = (sample_date + timedelta(days=i)).strftime('%Y-%m-%d')
        day_stats = stats["days"][day_key]
        center = next(p for p in day_stats["C"] if p["id"] == "1234")
        assert center["grade"] == grade, f"День {i+1}: ожидался грейд {grade}, получен {center['grade']}"

def test_update_player_stats_weekly_reset(stats_service, sample_team, sample_date, tmp_path):
    # Подготавливаем временный файл для тестов
    stats_file = tmp_path / "player_stats.json"
    with open(stats_file, 'w') as f:
        json.dump({"days": {}, "players": {}, "weekly_grades": {}}, f)

    # Обновляем статистику за три дня первой недели
    for i in range(3):  # Три дня подряд: common -> uncommon -> rare
        current_date = sample_date + timedelta(days=i)
        stats_service.update_player_stats(sample_team, current_date, str(stats_file))

    # Проверяем грейд в конце первой недели
    with open(stats_file) as f:
        stats = json.load(f)
    
    day_key = (sample_date + timedelta(days=2)).strftime('%Y-%m-%d')
    day_stats = stats["days"][day_key]
    center = next(p for p in day_stats["C"] if p["id"] == "1234")
    assert center["grade"] == "rare"  # После 3 попаданий - rare

    # Обновляем статистику в начале следующей недели
    next_week = sample_date + timedelta(days=7)
    stats_service.update_player_stats(sample_team, next_week, str(stats_file))

    # Проверяем, что грейд обнулился в новой неделе
    with open(stats_file) as f:
        stats = json.load(f)
    
    next_week_key = next_week.strftime('%Y-%m-%d')
    day_stats = stats["days"][next_week_key]
    center = next(p for p in day_stats["C"] if p["id"] == "1234")
    assert center["grade"] == "common"  # В новой неделе начинает с common 

def test_update_player_stats_duplicate_run(stats_service, sample_team, sample_date, tmp_path):
    # Подготавливаем временный файл для тестов
    stats_file = tmp_path / "player_stats.json"
    with open(stats_file, 'w') as f:
        json.dump({"days": {}, "players": {}, "weekly_grades": {}, "daily_appearances": {}}, f)

    # Запускаем обновление статистики дважды за один день
    for _ in range(2):
        stats_service.update_player_stats(sample_team, sample_date, str(stats_file))

    # Проверяем результаты
    with open(stats_file) as f:
        stats = json.load(f)

    day_key = sample_date.strftime('%Y-%m-%d')
    
    # Проверяем, что игрок учтен только один раз
    assert len(stats["daily_appearances"][day_key]) == 2  # Два игрока (C и G)
    
    # Проверяем статистику центрального нападающего
    day_stats = stats["days"][day_key]
    center = next(p for p in day_stats["C"] if p["id"] == "1234")
    assert center["grade"] == "common"  # Грейд не должен измениться после повторного запуска
    
    # Проверяем количество попаданий
    player_data = stats["players"]["1234"]
    assert player_data["weekly_appearances"] == 1  # Только одно попадание, несмотря на двойной запуск
    assert player_data["total_points"] == 10.5  # Очки не должны удваиваться 