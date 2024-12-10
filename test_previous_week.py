import json
import os
import asyncio
from datetime import datetime, timedelta
from app_day import main, MOSCOW_TIMEZONE, PLAYER_STATS_FILE

async def fetch_previous_week_data():
    # Определение предыдущей недели
    today = datetime.now(tz=MOSCOW_TIMEZONE)
    start_of_week = today - timedelta(days=today.weekday() + 7)
    end_of_week = start_of_week + timedelta(days=6)
    
    print(f"Fetching data for the week: {start_of_week.date()} to {end_of_week.date()}")
    
    current_day = start_of_week
    while current_day <= end_of_week:
        os.environ["CURRENT_DATE_OVERRIDE"] = current_day.strftime("%Y-%m-%d")
        print(f"Fetching data for {current_day.date()}")
        try:
            await main()  # Запуск основного скрипта
        except Exception as e:
            print(f"Error fetching data for {current_day.date()}: {e}")
        current_day += timedelta(days=1)

    print("Weekly data collection complete.")
    form_weekly_team(start_of_week, end_of_week)

def form_weekly_team(start_of_week, end_of_week):
    week_key = f"{start_of_week.strftime('%Y-%W')}"

    if not os.path.exists(PLAYER_STATS_FILE):
        print("Player stats file not found.")
        return

    with open(PLAYER_STATS_FILE, 'r') as f:
        stats = json.load(f)

    weekly_players = {}
    for player_id, data in stats.items():
        if player_id.isdigit() and data.get("team_of_the_day_count", 0) > 0:
            weekly_players[player_id] = {
                "name": data["name"],
                "team_of_the_day_count": data["team_of_the_day_count"],
                "grade": data["grade"]
            }

    # Сохраняем в weekly_stats
    stats["weekly_stats"] = stats.get("weekly_stats", {})
    stats["weekly_stats"][week_key] = {
        "start_date": start_of_week.strftime("%Y-%m-%d"),
        "end_date": end_of_week.strftime("%Y-%m-%d"),
        "players": weekly_players
    }

    with open(PLAYER_STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=4)

    print(f"Weekly team saved for {week_key}.")

if __name__ == "__main__":
    asyncio.run(fetch_previous_week_data())
