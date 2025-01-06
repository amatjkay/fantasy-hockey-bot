from datetime import datetime

# Даты сезона
SEASON_START = datetime(2024, 10, 4)
SEASON_END = datetime(2025, 4, 15)
INVALID_DATE = datetime(2024, 10, 3)

# Тестовые данные игроков
TEST_PLAYERS = {
    "123456": {
        "info": {
            "id": "123456",
            "name": "Test Player 1",
            "primary_position": 1,  # Center
            "team_id": "1"
        },
        "stats": {
            "total_points": 10.5,
            "goals": 2,
            "assists": 1,
            "shots": 5,
            "saves": 0,
            "goals_against": 0
        }
    },
    "234567": {
        "info": {
            "id": "234567",
            "name": "Test Player 2",
            "primary_position": 2,  # Left Wing
            "team_id": "2"
        },
        "stats": {
            "total_points": 8.5,
            "goals": 1,
            "assists": 2,
            "shots": 4,
            "saves": 0,
            "goals_against": 0
        }
    },
    "345678": {
        "info": {
            "id": "345678",
            "name": "Test Player 3",
            "primary_position": 3,  # Right Wing
            "team_id": "3"
        },
        "stats": {
            "total_points": 7.0,
            "goals": 1,
            "assists": 1,
            "shots": 3,
            "saves": 0,
            "goals_against": 0
        }
    },
    "456789": {
        "info": {
            "id": "456789",
            "name": "Test Player 4",
            "primary_position": 4,  # Defense
            "team_id": "4"
        },
        "stats": {
            "total_points": 6.5,
            "goals": 0,
            "assists": 2,
            "shots": 2,
            "saves": 0,
            "goals_against": 0
        }
    },
    "567890": {
        "info": {
            "id": "567890",
            "name": "Test Player 5",
            "primary_position": 4,  # Defense
            "team_id": "5"
        },
        "stats": {
            "total_points": 5.5,
            "goals": 1,
            "assists": 0,
            "shots": 3,
            "saves": 0,
            "goals_against": 0
        }
    },
    "678901": {
        "info": {
            "id": "678901",
            "name": "Test Player 6",
            "primary_position": 5,  # Goalie
            "team_id": "6"
        },
        "stats": {
            "total_points": 9.0,
            "goals": 0,
            "assists": 0,
            "shots": 0,
            "saves": 30,
            "goals_against": 2
        }
    }
}

# Тестовые данные для команды дня
TEST_TEAM_OF_DAY = {
    "date": datetime(2024, 10, 5),
    "total_points": 45,
    "players": [
        {
            "id": "3904173",
            "fullName": "Sebastian Aho",
            "defaultPositionId": 1,  # C
            "stats": {"points": 10}
        },
        {
            "id": "3891952",
            "fullName": "Artemi Panarin",
            "defaultPositionId": 2,  # LW
            "stats": {"points": 8}
        },
        {
            "id": "3899937",
            "fullName": "Mitch Marner",
            "defaultPositionId": 3,  # RW
            "stats": {"points": 12}
        },
        {
            "id": "3899978",
            "fullName": "Cale Makar",
            "defaultPositionId": 4,  # D
            "stats": {"points": 7}
        },
        {
            "id": "3899979",
            "fullName": "Victor Hedman",
            "defaultPositionId": 4,  # D
            "stats": {"points": 5}
        },
        {
            "id": "3899980",
            "fullName": "Andrei Vasilevskiy",
            "defaultPositionId": 5,  # G
            "stats": {"points": 3}
        }
    ]
}

# Тестовые данные для статистики
TEST_STATS = {
    "players": [
        {
            "id": "3904173",
            "fullName": "Sebastian Aho",
            "defaultPositionId": 1,
            "stats": {"points": 10, "goals": 2, "assists": 8}
        },
        {
            "id": "3891952",
            "fullName": "Artemi Panarin",
            "defaultPositionId": 2,
            "stats": {"points": 8, "goals": 1, "assists": 7}
        }
    ],
    "date": datetime(2024, 10, 5)
}

# Тестовые данные для недельной статистики
TEST_WEEKLY_STATS = {
    "start_date": datetime(2024, 10, 4),
    "end_date": datetime(2024, 10, 10),
    "players": [
        {
            "id": "3904173",
            "fullName": "Sebastian Aho",
            "defaultPositionId": 1,
            "stats": {"points": 15, "goals": 3, "assists": 12}
        },
        {
            "id": "3891952",
            "fullName": "Artemi Panarin",
            "defaultPositionId": 2,
            "stats": {"points": 12, "goals": 2, "assists": 10}
        }
    ]
} 