import requests
import json
from datetime import datetime, timedelta
import logging
from telegram import Bot
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import os
import asyncio
import pytz

# Конфигурация
LOG_FILE = "C:\\dev\\fantasy-hockey-bot\\log.txt"
MOSCOW_TIMEZONE = pytz.timezone('Europe/Moscow')
SEASON_START_DATE = datetime(2024, 10, 4)
SEASON_START_SCORING_PERIOD_ID = 0
LEAGUE_ID = 484910394
API_URL_TEMPLATE = 'https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/2025/segments/0/leagues/{league_id}?view=kona_player_info'
PLAYER_STATS_FILE = "player_stats.json"

POSITION_MAP = {
    1: 'C',
    2: 'LW',
    3: 'RW',
    4: 'D',
    5: 'G'
}

GRADE_COLORS = {
    "common": "black",
    "uncommon": "green",
    "rare": "blue",
    "epic": "purple",
    "legend": "orange"
}

# Логирование
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'  # Установите кодировку UTF-8
)

# Загрузка переменных окружения
load_dotenv('C:\\dev\\fantasy-hockey-bot\\.env')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

if not TELEGRAM_TOKEN or not CHAT_ID:
    logging.error("TELEGRAM_TOKEN или CHAT_ID не установлены в файле .env.")
    exit(1)

bot = Bot(token=TELEGRAM_TOKEN)

# Функция для расчета ID текущего периода
def calculate_scoring_period_id(current_date, season_start_date, season_start_scoring_period_id=1):
    if not isinstance(current_date, datetime):
        current_date = datetime.combine(current_date, datetime.min.time())
    
    # Убедитесь, что current_date имеет временную зону
    current_date = current_date.replace(tzinfo=MOSCOW_TIMEZONE)

    season_start_date = season_start_date.replace(tzinfo=MOSCOW_TIMEZONE)
    if current_date < season_start_date:
        logging.error("Текущая дата раньше даты начала сезона.")
        return None
    
    days_since_start = (current_date.date() - season_start_date.date()).days
    return season_start_scoring_period_id + days_since_start

# Обновление текущей недели
def update_week_period():
    today = datetime.now(MOSCOW_TIMEZONE).date()
    week_start = today - timedelta(days=today.weekday())  # Начало недели (понедельник)
    week_end = week_start + timedelta(days=6)  # Конец недели (воскресенье)

    if os.path.exists(PLAYER_STATS_FILE):
        with open(PLAYER_STATS_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {"current_week": {}, "players": {}}

    # Обнуление грейдов в начале новой недели
    if data.get("current_week", {}).get("start_date") != str(week_start):
        for player in data.get("players", {}).values():
            player["team_of_the_day_count"] = 0
            player["grade"] = "common"  # Обнуляем грейд
            player["team_of_the_day_dates"] = []  # Обнуляем даты

        data["current_week"] = {
            "start_date": str(week_start),
            "end_date": str(week_end)
        }
        with open(PLAYER_STATS_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    return week_start, week_end

# Определение грейда игрока на основе статистики
def calculate_grade(team_of_the_day_count):
    if team_of_the_day_count >= 5:
        return "legend"
    elif team_of_the_day_count >= 4:
        return "epic"
    elif team_of_the_day_count >= 3:
        return "rare"
    elif team_of_the_day_count >= 2:
        return "uncommon"
    else:
        return "common"

# Обновление статистики игроков, только для тех, кто попал в команду дня
def update_player_stats(player_id, name, date, applied_total, team_of_the_day=False):
    if os.path.exists(PLAYER_STATS_FILE):
        with open(PLAYER_STATS_FILE, 'r') as f:
            player_stats = json.load(f)
    else:
        player_stats = {"players": {}, "current_week": {}}

    if player_id not in player_stats["players"]:
        player_stats["players"][player_id] = {
            "name": name,
            "team_of_the_day_count": 1,
            "grade": "common",
            "team_of_the_day_dates": []
        }

    stats = player_stats["players"][player_id]
    stats["name"] = name

    if team_of_the_day and date not in stats["team_of_the_day_dates"]:
        stats["team_of_the_day_dates"].append(date)
        stats["team_of_the_day_count"] += 1
        stats["grade"] = calculate_grade(stats["team_of_the_day_count"])  # Обновляем грейд
        logging.info(f"Обновление грейда для игрока {name}: {stats['grade']}")  # Логирование обновления грейда

    with open(PLAYER_STATS_FILE, 'w') as f:
        json.dump(player_stats, f, indent=4)


# Получение данных игроков
def fetch_player_data(scoring_period_id, league_id):
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

# Разбор данных игроков
def parse_player_data(data, scoring_period_id):
    players_data = data.get('players', [])
    positions = {'C': [], 'LW': [], 'RW': [], 'D': [], 'G': []}

    try:
        player_stats = {}
        if os.path.exists(PLAYER_STATS_FILE):
            with open(PLAYER_STATS_FILE, 'r') as f:
                player_stats = json.load(f)
    except Exception as e:
        logging.warning(f"Ошибка при загрузке файла статистики игроков: {e}")

    for player_entry in players_data:
        player = player_entry.get('player', {})
        player_id = str(player.get('id', 'unknown'))
        name = player.get('fullName', 'Unknown')
        position_id = player.get('defaultPositionId', -1)
        position = POSITION_MAP.get(position_id, 'Unknown')
        image_url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/nhl/players/full/{player_id}.png&w=130&h=100"

        applied_total = 0
        for stat in player.get('stats', []):
            if stat.get('scoringPeriodId') == scoring_period_id:
                applied_total = round(stat.get('appliedTotal', 0), 2)
                break

        if position in positions:
            positions[position].append({
                'id': player_id,
                'name': name,
                'appliedTotal': applied_total,
                'image_url': image_url,
                'grade': player_stats.get("players", {}).get(player_id, {}).get("grade", "common")
            })

    return positions

# Создание коллажа
def create_collage(team):
    player_img_width, player_img_height = 130, 100
    padding = 20
    text_padding = 10
    line_height = player_img_height + text_padding + 30 + padding

    total_players = sum(len(players) for players in team.values())
    height = total_players * line_height + padding * 2
    width = 500

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    font_path = "C:\\Windows\\Fonts\\arial.ttf"  # Используем стандартный шрифт Arial
    font = ImageFont.truetype(font_path, size=20)

    y_offset = padding
    for position, players in team.items():
        for player in players:
            name = player['name']
            points = player['appliedTotal']
            image_url = player['image_url']
            grade = player['grade']
            color = GRADE_COLORS.get(grade, 'black')

            try:
                response = requests.get(image_url, stream=True, timeout=10)
                response.raise_for_status()
                player_image = Image.open(response.raw).convert("RGBA")
                bg = Image.new("RGBA", player_image.size, (255, 255, 255, 255))
                combined_image = Image.alpha_composite(bg, player_image)
                player_image = combined_image.convert("RGB").resize((player_img_width, player_img_height), Image.LANCZOS)
                image_x = (width - player_img_width) // 2
                image.paste(player_image, (image_x, y_offset))
            except Exception as e:
                logging.warning(f"Ошибка загрузки изображения для {name}: {e}")
                empty_img = Image.new("RGB", (player_img_width, player_img_height), "gray")
                image_x = (width - player_img_width) // 2
                image.paste(empty_img, (image_x, y_offset))

            text = f"{position}: {name} ({points:.2f} ftps)"
            text_width = draw.textlength(text, font=font)
            text_x = (width - text_width) // 2
            draw.text((text_x, y_offset + player_img_height + text_padding), text, fill=color, font=font)
            y_offset += line_height

    file_path = "C:\\dev\\fantasy-hockey-bot\\team_day_collage.jpg"
    image.save(file_path)
    return file_path

# Отправка коллажа в Telegram
async def send_collage(team):
    file_path = create_collage(team)
    if file_path:
        try:
            with open(file_path, "rb") as photo:
                await bot.send_photo(chat_id=CHAT_ID, photo=photo, caption="\U0001F3D2 Команда дня", parse_mode="HTML")
                logging.info("Коллаж успешно отправлен в Telegram.")
        except Exception as e:
            logging.error(f"Ошибка при отправке коллажа: {e}")
    else:
        await bot.send_message(chat_id=CHAT_ID, text="Не удалось создать коллаж.")

# Основная функция
async def main():
    week_start, week_end = update_week_period()

    current_date = week_start
    while current_date <= week_end:
        logging.info(f"Обработка данных для даты: {current_date}")

        scoring_period_id = calculate_scoring_period_id(current_date, SEASON_START_DATE, SEASON_START_SCORING_PERIOD_ID)

        if not scoring_period_id:
            logging.error(f"Не удалось рассчитать ID периода для даты: {current_date}")
            current_date += timedelta(days=1)
            continue

        data = fetch_player_data(scoring_period_id - 1, LEAGUE_ID)
        if not data:
            logging.error(f"Не удалось получить данные игроков для даты: {current_date}")
            current_date += timedelta(days=1)
            continue

        positions = parse_player_data(data, scoring_period_id - 1)
        team = {
            'C': sorted(positions['C'], key=lambda x: x['appliedTotal'], reverse=True)[:1],
            'LW': sorted(positions['LW'], key=lambda x: x['appliedTotal'], reverse=True)[:1],
            'RW': sorted(positions['RW'], key=lambda x: x['appliedTotal'], reverse=True)[:1],
            'D': sorted(positions['D'], key=lambda x: x['appliedTotal'], reverse=True)[:2],
            'G': sorted(positions['G'], key=lambda x: x['appliedTotal'], reverse=True)[:1]
        }

        for position, players in team.items():
            for player in players:
                if player['appliedTotal'] > 0:  # Проверка на 0 очков
                    logging.info(f"Обновление статистики для игрока: {player['name']} (ID: {player['id']}, Очки: {player['appliedTotal']})")
                    update_player_stats(player_id=player['id'], name=player['name'], date=str(current_date), applied_total=player['appliedTotal'], team_of_the_day=True)
                else:
                    logging.info(f"Игрок {player['name']} (ID: {player['id']}) пропущен из-за 0 очков.")

        await send_collage(team)
        logging.info(f"Сформирована команда дня для даты: {current_date}: {team}")

        current_date += timedelta(days=1)

# Запуск программы
if __name__ == "__main__":
    asyncio.run(main())
