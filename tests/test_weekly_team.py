import pytest
import json
import pytz
from datetime import datetime, timedelta
from src.services.stats_service import StatsService

@pytest.fixture
def stats_service():
    return StatsService()

@pytest.fixture
def sample_week_data():
    # Создаем тестовые данные для недели
    return {
        "days": {
            "2024-10-07": {  # Понедельник
                "C": [
                    {"id": "1", "name": "Player1", "points": 10, "grade": "common"},
                    {"id": "2", "name": "Player2", "points": 8, "grade": "common"}
                ],
                "LW": [
                    {"id": "3", "name": "Player3", "points": 7, "grade": "common"}
                ],
                "RW": [
                    {"id": "4", "name": "Player4", "points": 12, "grade": "common"}
                ],
                "D": [
                    {"id": "5", "name": "Player5", "points": 6, "grade": "common"},
                    {"id": "6", "name": "Player6", "points": 5, "grade": "common"}
                ],
                "G": [
                    {"id": "7", "name": "Player7", "points": 8, "grade": "common"}
                ]
            },
            "2024-10-08": {  # Вторник
                "C": [
                    {"id": "1", "name": "Player1", "points": 15, "grade": "uncommon"},
                    {"id": "8", "name": "Player8", "points": 9, "grade": "common"}
                ],
                "LW": [
                    {"id": "3", "name": "Player3", "points": 11, "grade": "uncommon"}
                ],
                "RW": [
                    {"id": "9", "name": "Player9", "points": 25, "grade": "common"}
                ],
                "D": [
                    {"id": "5", "name": "Player5", "points": 8, "grade": "uncommon"}
                ],
                "G": [
                    {"id": "7", "name": "Player7", "points": 10, "grade": "uncommon"}
                ]
            },
            "2024-10-09": {  # Среда
                "C": [
                    {"id": "1", "name": "Player1", "points": 12, "grade": "rare"}
                ],
                "LW": [
                    {"id": "3", "name": "Player3", "points": 9, "grade": "rare"}
                ],
                "RW": [
                    {"id": "4", "name": "Player4", "points": 8, "grade": "uncommon"}
                ],
                "D": [
                    {"id": "5", "name": "Player5", "points": 7, "grade": "rare"}
                ],
                "G": [
                    {"id": "10", "name": "Player10", "points": 30, "grade": "common"}
                ]
            }
        },
        "players": {
            "1": {
                "name": "Player1",
                "total_points": 37,
                "grade": "rare",
                "weekly_appearances": 3,
                "appearances": {
                    "2024-10-07": {"points": 10},
                    "2024-10-08": {"points": 15},
                    "2024-10-09": {"points": 12}
                }
            },
            "2": {
                "name": "Player2",
                "total_points": 8,
                "grade": "common",
                "weekly_appearances": 1,
                "appearances": {
                    "2024-10-07": {"points": 8}
                }
            },
            "3": {
                "name": "Player3",
                "total_points": 27,
                "grade": "rare",
                "weekly_appearances": 3,
                "appearances": {
                    "2024-10-07": {"points": 7},
                    "2024-10-08": {"points": 11},
                    "2024-10-09": {"points": 9}
                }
            },
            "4": {
                "name": "Player4",
                "total_points": 20,
                "grade": "uncommon",
                "weekly_appearances": 2,
                "appearances": {
                    "2024-10-07": {"points": 12},
                    "2024-10-09": {"points": 8}
                }
            },
            "5": {
                "name": "Player5",
                "total_points": 21,
                "grade": "rare",
                "weekly_appearances": 3,
                "appearances": {
                    "2024-10-07": {"points": 6},
                    "2024-10-08": {"points": 8},
                    "2024-10-09": {"points": 7}
                }
            },
            "6": {
                "name": "Player6",
                "total_points": 5,
                "grade": "common",
                "weekly_appearances": 1,
                "appearances": {
                    "2024-10-07": {"points": 5}
                }
            },
            "7": {
                "name": "Player7",
                "total_points": 18,
                "grade": "uncommon",
                "weekly_appearances": 2,
                "appearances": {
                    "2024-10-07": {"points": 8},
                    "2024-10-08": {"points": 10}
                }
            },
            "8": {
                "name": "Player8",
                "total_points": 9,
                "grade": "common",
                "weekly_appearances": 1,
                "appearances": {
                    "2024-10-08": {"points": 9}
                }
            },
            "9": {
                "name": "Player9",
                "total_points": 25,
                "grade": "common",
                "weekly_appearances": 1,
                "appearances": {
                    "2024-10-08": {"points": 25}
                }
            },
            "10": {
                "name": "Player10",
                "total_points": 30,
                "grade": "common",
                "weekly_appearances": 1,
                "appearances": {
                    "2024-10-09": {"points": 30}
                }
            }
        }
    }

def test_form_weekly_team_grade_priority(stats_service, sample_week_data, tmp_path):
    """Тест приоритета по грейду при формировании команды недели"""
    # Подготавливаем файл с данными
    stats_file = tmp_path / "stats.json"
    with open(stats_file, "w") as f:
        json.dump(sample_week_data, f)

    # Формируем команду недели
    week_start = datetime(2024, 10, 7, tzinfo=pytz.UTC)
    weekly_team = stats_service.form_weekly_team(week_start, str(stats_file))

    # Проверяем, что игроки с более высоким грейдом попали в команду
    assert weekly_team["C"][0]["id"] == "1"  # Player1 (rare)
    assert weekly_team["LW"][0]["id"] == "3"  # Player3 (rare)
    assert weekly_team["D"][0]["id"] == "5"  # Player5 (rare)

def test_form_weekly_team_points_override(stats_service, sample_week_data, tmp_path):
    """Тест приоритета по очкам при значительном преимуществе"""
    # Подготавливаем файл с данными
    stats_file = tmp_path / "stats.json"
    with open(stats_file, "w") as f:
        json.dump(sample_week_data, f)

    # Проверяем, что Player4 (uncommon с 20 очками) попал в команду,
    # так как 25 очков Player9 (common) не превышают 20*2=40 очков
    week_start = datetime(2024, 10, 7, tzinfo=pytz.UTC)
    weekly_team = stats_service.form_weekly_team(week_start, str(stats_file))

    assert weekly_team["RW"][0]["id"] == "4"  # Player4 (uncommon) имеет приоритет
    assert weekly_team["G"][0]["id"] == "7"  # Player7 (uncommon) имеет приоритет

def test_form_weekly_team_composition(stats_service, sample_week_data, tmp_path):
    """Тест правильности состава команды недели"""
    # Подготавливаем файл с данными
    stats_file = tmp_path / "stats.json"
    with open(stats_file, "w") as f:
        json.dump(sample_week_data, f)

    # Формируем команду недели
    week_start = datetime(2024, 10, 7, tzinfo=pytz.UTC)
    weekly_team = stats_service.form_weekly_team(week_start, str(stats_file))

    # Проверяем состав команды
    assert len(weekly_team["C"]) == 1  # 1 центральный
    assert len(weekly_team["LW"]) == 1  # 1 левый крайний
    assert len(weekly_team["RW"]) == 1  # 1 правый крайний
    assert len(weekly_team["D"]) == 2  # 2 защитника
    assert len(weekly_team["G"]) == 1  # 1 вратарь

def test_form_weekly_team_empty_week(stats_service, tmp_path):
    """Тест обработки пустой недели"""
    # Подготавливаем пустой файл с данными
    stats_file = tmp_path / "stats.json"
    with open(stats_file, "w") as f:
        json.dump({"days": {}, "players": {}}, f)

    # Формируем команду недели
    week_start = datetime(2024, 10, 7, tzinfo=pytz.UTC)
    weekly_team = stats_service.form_weekly_team(week_start, str(stats_file))

    # Проверяем, что все позиции существуют, но пусты
    assert all(pos in weekly_team for pos in ["C", "LW", "RW", "D", "G"])
    assert all(len(weekly_team[pos]) == 0 for pos in weekly_team)

def test_form_weekly_team_partial_week(stats_service, sample_week_data, tmp_path):
    """Тест формирования команды для неполной недели"""
    # Оставляем только два дня
    partial_data = {
        "days": {
            k: v for k, v in sample_week_data["days"].items() 
            if k in ["2024-10-07", "2024-10-08"]
        },
        "players": sample_week_data["players"]
    }

    # Подготавливаем файл с данными
    stats_file = tmp_path / "stats.json"
    with open(stats_file, "w") as f:
        json.dump(partial_data, f)

    # Формируем команду недели
    week_start = datetime(2024, 10, 7, tzinfo=pytz.UTC)
    weekly_team = stats_service.form_weekly_team(week_start, str(stats_file))

    # Проверяем, что команда сформирована из доступных данных
    assert len(weekly_team["C"]) > 0
    assert len(weekly_team["LW"]) > 0
    assert len(weekly_team["RW"]) > 0
    assert len(weekly_team["D"]) > 0
    assert len(weekly_team["G"]) > 0 

def test_form_weekly_team_appearances_history(stats_service, sample_week_data, tmp_path):
    """Тест проверки истории попаданий в команду дня"""
    # Подготавливаем файл с данными
    stats_file = tmp_path / "stats.json"
    with open(stats_file, "w") as f:
        json.dump(sample_week_data, f)

    # Формируем команду недели
    week_start = datetime(2024, 10, 7, tzinfo=pytz.UTC)
    weekly_team = stats_service.form_weekly_team(week_start, str(stats_file))

    # Проверяем Player1 (центральный нападающий)
    player1 = weekly_team["C"][0]
    assert player1["id"] == "1"
    assert player1["weekly_appearances"] == 3  # Попал в команду 7, 8 и 9 октября
    assert len(player1["appearances"]) == 3
    assert "2024-10-07" in player1["appearances"]
    assert "2024-10-08" in player1["appearances"]
    assert "2024-10-09" in player1["appearances"]
    assert player1["appearances"]["2024-10-07"]["points"] == 10
    assert player1["appearances"]["2024-10-08"]["points"] == 15
    assert player1["appearances"]["2024-10-09"]["points"] == 12

    # Проверяем Player3 (левый нападающий)
    player3 = weekly_team["LW"][0]
    assert player3["id"] == "3"
    assert player3["weekly_appearances"] == 3
    assert len(player3["appearances"]) == 3
    assert player3["appearances"]["2024-10-07"]["points"] == 7
    assert player3["appearances"]["2024-10-08"]["points"] == 11
    assert player3["appearances"]["2024-10-09"]["points"] == 9

    # Проверяем Player5 (защитник)
    player5 = weekly_team["D"][0]
    assert player5["id"] == "5"
    assert player5["weekly_appearances"] == 3
    assert len(player5["appearances"]) == 3
    assert player5["appearances"]["2024-10-07"]["points"] == 6
    assert player5["appearances"]["2024-10-08"]["points"] == 8
    assert player5["appearances"]["2024-10-09"]["points"] == 7 