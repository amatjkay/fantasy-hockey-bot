import pytest
import json
import pytz
from datetime import datetime
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

def test_update_player_stats_new_week(stats_service, sample_team, sample_date, tmp_path):
    # Подготавливаем временный файл для тестов
    stats_file = tmp_path / "player_stats.json"
    with open(stats_file, 'w') as f:
        json.dump({"weeks": {}}, f)

    # Обновляем статистику
    stats_service.update_player_stats(sample_team, sample_date, str(stats_file))

    # Проверяем результаты
    with open(stats_file) as f:
        stats = json.load(f)

    assert "weeks" in stats
    week_key = "2024-10-07_2024-10-13"
    assert week_key in stats["weeks"]
    assert "players" in stats["weeks"][week_key]
    assert len(stats["weeks"][week_key]["players"]) == 2

def test_update_player_stats_grade_progression(stats_service, sample_team, sample_date, tmp_path):
    # Подготавливаем временный файл для тестов
    stats_file = tmp_path / "player_stats.json"
    with open(stats_file, 'w') as f:
        json.dump({"weeks": {}}, f)

    # Обновляем статистику несколько раз
    for _ in range(3):
        stats_service.update_player_stats(sample_team, sample_date, str(stats_file))

    # Проверяем результаты
    with open(stats_file) as f:
        stats = json.load(f)

    week_key = "2024-10-07_2024-10-13"
    players = stats["weeks"][week_key]["players"]
    assert len(players) == 2
    for player in players:
        assert "grade" in player
        assert player["grade"] in ["common", "rare", "epic", "legendary"]

def test_update_player_stats_weekly_reset(stats_service, sample_team, sample_date, tmp_path):
    # Подготавливаем временный файл для тестов
    stats_file = tmp_path / "player_stats.json"
    with open(stats_file, 'w') as f:
        json.dump({"weeks": {}}, f)

    # Обновляем статистику для первой недели
    stats_service.update_player_stats(sample_team, sample_date, str(stats_file))

    # Обновляем статистику для следующей недели
    next_week = datetime(2024, 10, 14, tzinfo=pytz.UTC)
    stats_service.update_player_stats(sample_team, next_week, str(stats_file))

    # Проверяем результаты
    with open(stats_file) as f:
        stats = json.load(f)

    assert "2024-10-07_2024-10-13" in stats["weeks"]
    assert "2024-10-14_2024-10-20" in stats["weeks"]
    for week in stats["weeks"].values():
        assert "players" in week
        assert len(week["players"]) == 2 