import requests
import json
from datetime import datetime, timedelta
import logging
import time
from telegram import Bot
from dotenv import load_dotenv
import os
import asyncio

# Константы
LOG_FILE = "/home/lex/dev/bot/fantasy-hockey-bot/last_run.log"
SEASON_START_DATE = datetime(2024, 10, 4)  # Дата начала сезона
SEASON_START_SCORING_PERIOD_ID = 1  # ScoringPeriodId для начала сезона
LEAGUE_ID = 484910394  # League ID
API_URL_TEMPLATE = 'https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/2025/segments/0/leagues/{league_id}?view=kona_player_info'

# Соответствие defaultPositionId и позиций
POSITION_MAP = {
    1: 'C',    # Центр
    2: 'LW',   # Левый нападающий
    3: 'RW',   # Правый нападающий
    4: 'D',    # Защитник
    5: 'G'     # Вратарь
}

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Загрузка переменных окружения
load_dotenv('/home/lex/dev/bot/fantasy-hockey-bot/.env')

# Telegram Bot Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

if not TELEGRAM_TOKEN or not CHAT_ID:
    logging.error("TELEGRAM_TOKEN или CHAT_ID не установлены в файле .env.")
    exit(1)

bot = Bot(token=TELEGRAM_TOKEN)

# Проверка, была ли задача выполнена за последние 24 часа
# def was_task_executed_recently():
#     if os.path.exists(LOG_FILE):
#         last_run_time = os.path.getmtime(LOG_FILE)
#         if time.time() - last_run_time < 86400:  # 24 часа
#             return True
#     return False

# if was_task_executed_recently():
#     logging.info("Задача уже была выполнена в последние 24 часа. Завершаем.")
#     exit(0)

# Логируем выполнение задачи
with open(LOG_FILE, "w") as log_file:
    log_file.write("Task executed at: " + time.ctime())

# Отправка сообщения в Telegram
async def send_telegram_message(message: str):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
        logging.info("Сообщение успешно отправлено в Telegram.")
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения в Telegram: {e}")

# Вычисление scoringPeriodId
def calculate_scoring_period_id(current_date, season_start_date, season_start_scoring_period_id=1):
    if current_date < season_start_date:
        logging.error("Текущая дата раньше даты начала сезона.")
        return None
    days_since_start = (current_date.date() - season_start_date.date()).days
    current_scoring_period_id = season_start_scoring_period_id + days_since_start
    logging.info(f"Вычислен current_scoring_period_id: {current_scoring_period_id}")
    return current_scoring_period_id

# Получение данных игроков
def fetch_player_data(scoring_period_id, league_id):
    base_headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0',
    }

    filters = {
        "players": {
            "filterSlotIds": {"value": [0, 6, 1, 2, 4, 5]},  # Все позиции
            "filterStatsForCurrentSeasonScoringPeriodId": {"value": [scoring_period_id]},
            "sortAppliedStatTotalForScoringPeriodId": {"sortAsc": False, "sortPriority": 2, "value": scoring_period_id},
            "limit": 50
        }
    }

    url = API_URL_TEMPLATE.format(league_id=league_id)

    for attempt in range(3):
        try:
            headers = base_headers.copy()
            headers['x-fantasy-filter'] = json.dumps(filters)
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.warning(f"Попытка {attempt + 1} не удалась: {e}")
            time.sleep(5)

    logging.error("Не удалось получить данные игроков после 3 попыток.")
    return None

# Парсинг данных игроков
def parse_player_data(data, scoring_period_id):
    players_data = data.get('players', [])
    positions = {'C': [], 'LW': [], 'RW': [], 'D': [], 'G': []}

    for player_entry in players_data:
        player = player_entry.get('player', {})
        name = player.get('fullName', 'Unknown')
        position_id = player.get('defaultPositionId', -1)
        position = POSITION_MAP.get(position_id, 'Unknown')

        applied_total = 0
        for stat in player.get('stats', []):
            if stat.get('scoringPeriodId') == scoring_period_id:
                applied_total = round(stat.get('appliedTotal', 0), 2)
                break

        if position in positions:
            positions[position].append({'name': name, 'appliedTotal': applied_total})

    return positions

# Составление команды дня
def assemble_team(positions):
    return {
        'C': sorted(positions['C'], key=lambda x: x['appliedTotal'], reverse=True)[:1],
        'LW': sorted(positions['LW'], key=lambda x: x['appliedTotal'], reverse=True)[:1],
        'RW': sorted(positions['RW'], key=lambda x: x['appliedTotal'], reverse=True)[:1],
        'D': sorted(positions['D'], key=lambda x: x['appliedTotal'], reverse=True)[:2],
        'G': sorted(positions['G'], key=lambda x: x['appliedTotal'], reverse=True)[:1]
    }

# Формирование сообщения
async def display_team(team):
    """
    Формирует сообщение о "команде дня" с улучшенным дизайном и отправляет его в Telegram.
    """
    message = "<b>🏒 Команда дня:</b>\n\n"

    # Нападающие
    message += "🎯 <b>Нападающие:</b>\n"
    center = team['C'][0] if team['C'] else None
    lw = team['LW'][0] if team['LW'] else None
    rw = team['RW'][0] if team['RW'] else None

    if center:
        message += f"  C: {center['name']} - <i>{center['appliedTotal']} ftps</i>\n"
    else:
        message += "  C: Нет данных\n"

    if lw:
        message += f"  LW: {lw['name']} - <i>{lw['appliedTotal']} ftps</i>\n"
    else:
        message += "  LW: Нет данных\n"

    if rw:
        message += f"  RW: {rw['name']} - <i>{rw['appliedTotal']} ftps</i>\n"
    else:
        message += "  RW: Нет данных\n"

    # Защитники
    message += "\n🛡 <b>Защитники:</b>\n"
    if team['D']:
        for idx, d_player in enumerate(team['D'], 1):
            message += f"  D{idx}: {d_player['name']} - <i>{d_player['appliedTotal']} ftps</i>\n"
    else:
        message += "  D: Нет данных\n"

    # Вратарь
    message += "\n🥅 <b>Вратарь:</b>\n"
    goalie = team['G'][0] if team['G'] else None
    if goalie:
        message += f"  G: {goalie['name']} - <i>{goalie['appliedTotal']} ftps</i>\n"
    else:
        message += "  G: Нет данных\n"

    # Отправка сообщения
    await send_telegram_message(message)


# Основная логика
async def main():
    current_date = datetime.now()
    logging.info(f"Текущая дата: {current_date}")

    scoring_period_id = calculate_scoring_period_id(current_date, SEASON_START_DATE, SEASON_START_SCORING_PERIOD_ID)
    if not scoring_period_id:
        return

    data = fetch_player_data(scoring_period_id - 1, LEAGUE_ID)
    if not data:
        await send_telegram_message("Не удалось получить данные о команде дня.")
        return

    positions = parse_player_data(data, scoring_period_id - 1)
    team = assemble_team(positions)

    await display_team(team)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
