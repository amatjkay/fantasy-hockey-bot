import requests
import json
from datetime import datetime
import logging
from telegram import Bot
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import os
import asyncio
import time
import pytz

# Конфигурация
LOG_FILE = "/home/lex/dev/bot/fantasy-hockey-bot/last_run.log"
MOSCOW_TIMEZONE = pytz.timezone('Europe/Moscow')
SEASON_START_DATE = datetime(2024, 10, 4)
SEASON_START_SCORING_PERIOD_ID = 1
LEAGUE_ID = 484910394
API_URL_TEMPLATE = 'https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/2025/segments/0/leagues/{league_id}?view=kona_player_info'

# Карта позиций
POSITION_MAP = {
    1: 'C',   # Центр
    2: 'LW',  # Левый нападающий
    3: 'RW',  # Правый нападающий
    4: 'D',   # Защитник
    5: 'G'    # Вратарь
}

# Логирование
logging.basicConfig(
    filename="/home/lex/dev/bot/fantasy-hockey-bot/log.txt",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Загрузка переменных окружения
load_dotenv('/home/lex/dev/bot/fantasy-hockey-bot/.env')

# Telegram Bot
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

if not TELEGRAM_TOKEN or not CHAT_ID:
    logging.error("TELEGRAM_TOKEN или CHAT_ID не установлены в файле .env.")
    exit(1)

bot = Bot(token=TELEGRAM_TOKEN)


# def was_task_executed_today_at_nine():
#     """
#     Проверяет, была ли задача выполнена сегодня в 9:00 по Москве.
#     """
#     if os.path.exists(LOG_FILE):
#         with open(LOG_FILE, "r") as log_file:
#             last_run_timestamp = log_file.read().strip()

#         try:
#             last_run_time = datetime.fromtimestamp(float(last_run_timestamp), tz=MOSCOW_TIMEZONE)
#             current_time = datetime.now(tz=MOSCOW_TIMEZONE)

#             if (
#                 last_run_time.date() == current_time.date() and
#                 last_run_time.hour == 9
#             ):
#                 return True
#         except ValueError:
#             logging.warning("Ошибка чтения времени выполнения из лог-файла.")
#     return False


def log_task_execution():
    """
    Логирует текущее время выполнения задачи.
    """
    with open(LOG_FILE, "w") as log_file:
        log_file.write(str(time.time()))


def calculate_scoring_period_id(current_date, season_start_date, season_start_scoring_period_id=1):
    """
    Вычисляет текущий scoringPeriodId.
    """
    if current_date < season_start_date:
        logging.error("Текущая дата раньше даты начала сезона.")
        return None
    days_since_start = (current_date.date() - season_start_date.date()).days
    return season_start_scoring_period_id + days_since_start


def fetch_player_data(scoring_period_id, league_id):
    """
    Запрашивает данные о игроках.
    """
    base_headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0',
    }

    filters = {
        "players": {
            "filterSlotIds": {"value": [0, 6, 1, 2, 4, 5]},
            "filterStatsForCurrentSeasonScoringPeriodId": {"value": [scoring_period_id]},
            "sortAppliedStatTotalForScoringPeriodId": {"sortAsc": False, "sortPriority": 2, "value": scoring_period_id},
            "limit": 50
        }
    }

    url = API_URL_TEMPLATE.format(league_id=league_id)

    try:
        headers = base_headers.copy()
        headers['x-fantasy-filter'] = json.dumps(filters)
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при запросе данных игроков: {e}")
        return None


def parse_player_data(data, scoring_period_id):
    """
    Парсит данные игроков и распределяет их по позициям.
    """
    players_data = data.get('players', [])
    positions = {'C': [], 'LW': [], 'RW': [], 'D': [], 'G': []}

    for player_entry in players_data:
        player = player_entry.get('player', {})
        name = player.get('fullName', 'Unknown')
        position_id = player.get('defaultPositionId', -1)
        position = POSITION_MAP.get(position_id, 'Unknown')
        image_url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/nhl/players/full/{player.get('id', 'unknown')}.png&w=130&h=100"

        applied_total = 0
        for stat in player.get('stats', []):
            if stat.get('scoringPeriodId') == scoring_period_id:
                applied_total = round(stat.get('appliedTotal', 0), 2)
                break

        if position in positions:
            positions[position].append({
                'name': name,
                'appliedTotal': applied_total,
                'image_url': image_url
            })

    return positions


def assemble_team(positions):
    """
    Составляет команду дня.
    """
    return {
        'C': sorted(positions['C'], key=lambda x: x['appliedTotal'], reverse=True)[:1],
        'LW': sorted(positions['LW'], key=lambda x: x['appliedTotal'], reverse=True)[:1],
        'RW': sorted(positions['RW'], key=lambda x: x['appliedTotal'], reverse=True)[:1],
        'D': sorted(positions['D'], key=lambda x: x['appliedTotal'], reverse=True)[:2],
        'G': sorted(positions['G'], key=lambda x: x['appliedTotal'], reverse=True)[:1]
    }


def create_collage(team):
    """
    Создает изображение с коллажем команды.
    """
    player_img_width, player_img_height = 130, 100
    padding = 20
    text_padding = 10
    line_height = player_img_height + text_padding + 30 + padding

    total_players = sum(len(players) for players in team.values())
    height = total_players * line_height + padding * 2

    width = 500
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    font_path = "/usr/share/fonts/ttf/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, size=20)

    y_offset = padding
    for position, players in team.items():
        for player in players:
            name = player['name']
            points = player['appliedTotal']
            image_url = player['image_url']

            try:
                response = requests.get(image_url, stream=True, timeout=10)
                response.raise_for_status()
                player_image = Image.open(response.raw).convert("RGBA")
                bg = Image.new("RGB", player_image.size, (255, 255, 255))
                player_image = Image.alpha_composite(bg.convert("RGBA"), player_image).convert("RGB")
                player_image = player_image.resize((player_img_width, player_img_height), Image.LANCZOS)

                image_x = (width - player_img_width) // 2
                image.paste(player_image, (image_x, y_offset))
            except Exception as e:
                logging.warning(f"Ошибка загрузки изображения для {name}: {e}")
                empty_img = Image.new("RGB", (player_img_width, player_img_height), "gray")
                image_x = (width - player_img_width) // 2
                image.paste(empty_img, (image_x, y_offset))

            text = f"{position}: {name} ({points} ftps)"
            text_width = draw.textlength(text, font=font)
            text_x = (width - text_width) // 2
            draw.text((text_x, y_offset + player_img_height + text_padding), text, fill="black", font=font)

            y_offset += line_height

    file_path = "/home/lex/dev/bot/fantasy-hockey-bot/team_collage.jpg"
    image.save(file_path)
    return file_path


async def send_collage(team):
    """
    Отправляет коллаж с командой в Telegram.
    """
    file_path = create_collage(team)
    try:
        with open(file_path, "rb") as photo:
            await bot.send_photo(chat_id=CHAT_ID, photo=photo, caption="🏒 <b>Команда дня</b>", parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка при отправке изображения: {e}")


async def main():
    current_date = datetime.now()
    scoring_period_id = calculate_scoring_period_id(current_date, SEASON_START_DATE, SEASON_START_SCORING_PERIOD_ID)
    if not scoring_period_id:
        return

    data = fetch_player_data(scoring_period_id - 1, LEAGUE_ID)
    if not data:
        return

    positions = parse_player_data(data, scoring_period_id - 1)
    team = assemble_team(positions)
    await send_collage(team)


if __name__ == "__main__":
    # if was_task_executed_today_at_nine():
    #     print("Задача уже была выполнена сегодня в 9:00 по Москве. Завершаем.")
    #     exit(0)
    log_task_execution()
    asyncio.run(main())

