import json
import os
import asyncio
from datetime import datetime, timedelta
from app_day import main, MOSCOW_TIMEZONE, SEASON_START_DATE, SEASON_START_SCORING_PERIOD_ID

async def fetch_data_from_season_start():
    # Определяем дату начала сезона и вчерашнюю дату
    start_date = SEASON_START_DATE.date()  # Преобразуем в date
    end_date = (datetime.now(tz=MOSCOW_TIMEZONE) - timedelta(days=1)).date()  # Преобразуем в date

    print(f"Fetching data from {start_date} to {end_date}")

    current_day = start_date
    while current_day <= end_date:
        os.environ["CURRENT_DATE_OVERRIDE"] = current_day.strftime("%Y-%m-%d")
        print(f"Fetching data for {current_day}")

        try:
            await main()  # Запускаем сбор данных за текущий день
        except Exception as e:
            print(f"Error fetching data for {current_day}: {e}")

        # Переходим к следующему дню
        current_day += timedelta(days=1)

        # Сохраняем коллаж с уникальным именем
        save_screenshot(current_day)

    print("Data collection complete.")

def save_screenshot(date):
    # Папка для сохранения скриншотов
    screenshots_dir = "/home/lex/dev/bot/fantasy-hockey-bot/screenshots/"
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)

    # Путь для сохранения скриншота
    screenshot_path = os.path.join(screenshots_dir, f"team_day_{date}.jpg")

    # Переименовываем и сохраняем файл
    original_path = "/home/lex/dev/bot/fantasy-hockey-bot/team_day_collage.jpg"
    if os.path.exists(original_path):
        os.rename(original_path, screenshot_path)
        print(f"Screenshot saved: {screenshot_path}")
    else:
        print(f"No screenshot found for {date}")

if __name__ == "__main__":
    asyncio.run(fetch_data_from_season_start())
