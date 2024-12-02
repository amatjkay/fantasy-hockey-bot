import requests
import json
from datetime import datetime, timedelta

# Установите дату начала сезона и соответствующий ей scoringPeriodId
season_start_date = datetime(2024, 10, 4)  # Замените на фактическую дату начала сезона
season_start_scoring_period_id = 1  # Замените на фактический scoringPeriodId начала сезона

# Определяем текущую дату и предыдущую дату
current_date = datetime.now()
previous_date = current_date - timedelta(days=1)

# Вычисляем current_scoring_period_id на основе текущей даты
days_since_season_start = (current_date.date() - season_start_date.date()).days
current_scoring_period_id = season_start_scoring_period_id + days_since_season_start

# Вычисляем previous_scoring_period_id для предыдущей даты
previous_scoring_period_id = current_scoring_period_id - 1

# Формируем заголовки запроса
headers = {
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0',
    'x-fantasy-filter': json.dumps({
        "players": {
            "filterSlotIds": {"value": [0, 1, 2, 3, 4, 5]},
            "filterStatsForCurrentSeasonScoringPeriodId": {"value": [previous_scoring_period_id]},
            "sortAppliedStatTotalForScoringPeriodId": {
                "sortAsc": False,
                "sortPriority": 2,
                "value": previous_scoring_period_id
            },
            "limit": 100  # Увеличиваем лимит для большей выборки игроков
        }
    })
}

# URL API
url = 'https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/2025/segments/0/leagues/484910394?view=kona_player_info'

# Выполняем запрос
response = requests.get(url, headers=headers)

# Проверяем статус ответа
if response.status_code == 200:
    data = response.json()
else:
    print(f"Ошибка: Получен статус {response.status_code}")
    data = None

# Парсим и обрабатываем данные
if data:
    players_data = data.get('players', [])

    forwards = []
    defensemen = []
    goalies = []

    position_map = {
        1: 'C',
        2: 'LW',
        3: 'RW',
        4: 'D',
        5: 'G'
    }

    for player_entry in players_data:
        player = player_entry.get('player', {})
        name = player.get('fullName', 'Unknown')
        position_id = player.get('defaultPositionId', -1)
        position = position_map.get(position_id, 'Unknown')

        stats = player.get('stats', [])
        applied_total = 0
        for stat in stats:
            if stat.get('scoringPeriodId') == previous_scoring_period_id:
                applied_total = round(stat.get('appliedTotal', 0), 2)
                break

        player_info = {
            'name': name,
            'position': position,
            'appliedTotal': applied_total
        }

        if position in ['C', 'LW', 'RW']:
            forwards.append(player_info)
        elif position == 'D':
            defensemen.append(player_info)
        elif position == 'G':
            goalies.append(player_info)

    # Сортируем списки игроков по appliedTotal в порядке убывания
    forwards_sorted = sorted(forwards, key=lambda x: x['appliedTotal'], reverse=True)
    defensemen_sorted = sorted(defensemen, key=lambda x: x['appliedTotal'], reverse=True)
    goalies_sorted = sorted(goalies, key=lambda x: x['appliedTotal'], reverse=True)

    # Выбираем лучших игроков
    top_forwards = forwards_sorted[:3]
    top_defensemen = defensemen_sorted[:2]
    top_goalie = goalies_sorted[:1]

    print("Команда дня:")
    print("\n==========")
    for player in top_forwards:
        print(f"{player['name']} ({player['position']}): {player['appliedTotal']} fpts")

    print("\n==========")
    for player in top_defensemen:
        print(f"{player['name']} ({player['position']}): {player['appliedTotal']} fpts")

    print("\n==========")
    if top_goalie:
        goalie = top_goalie[0]
        print(f"{goalie['name']} ({goalie['position']}): {goalie['appliedTotal']} fpts")
    else:
        print("Данных о вратарях нет.")
else:
    print("Нет данных для отображения.")
