import requests
import json
from datetime import datetime, timedelta
import logging
import time
from telegram import Bot
from dotenv import load_dotenv
import os
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Загрузка переменных из .env файла
load_dotenv()

# Конфигурация
SEASON_START_DATE = datetime(2024, 10, 4)  # Обновите при необходимости
SEASON_START_SCORING_PERIOD_ID = 1  # Обновите при необходимости
LEAGUE_ID = 484910394  # Обновите на ваш League ID
API_URL_TEMPLATE = 'https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/2025/segments/0/leagues/{league_id}?view=kona_player_info'

# Соответствие defaultPositionId и позиций
POSITION_MAP = {
    1: 'C',    # Центр
    2: 'LW',   # Левый нападающий
    3: 'RW',   # Правый нападающий
    4: 'D',    # Защитник
    5: 'G'     # Вратарь
}

# Telegram Bot Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

if not TELEGRAM_TOKEN or not CHAT_ID:
    logging.error("TELEGRAM_TOKEN или CHAT_ID не установлены в файле .env.")
    exit(1)

bot = Bot(token=TELEGRAM_TOKEN)

# Константы для повторных попыток
MAX_RETRIES = 3
RETRY_DELAY = 5  # секунд

async def send_telegram_message(message: str):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
        logging.info("Сообщение успешно отправлено в Telegram.")
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения в Telegram: {e}")

def calculate_scoring_period_id(current_date, season_start_date, season_start_scoring_period_id=1):
    """
    Вычисляет текущий scoringPeriodId на основе даты начала сезона и текущей даты.
    Предполагается, что scoringPeriodId увеличивается на 1 каждый день.
    """
    if current_date < season_start_date:
        logging.error("Текущая дата раньше даты начала сезона.")
        return None
    days_since_start = (current_date.date() - season_start_date.date()).days
    current_scoring_period_id = season_start_scoring_period_id + days_since_start
    logging.info(f"Вычислен current_scoring_period_id: {current_scoring_period_id}")
    return current_scoring_period_id

def fetch_player_data(scoring_period_id, league_id):
    """
    Выполняет запросы к API ESPN и возвращает данные о игроках.
    Делает отдельные запросы для полевых игроков и вратарей.
    """
    base_headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0',
    }

    # Фильтр для полевых игроков (C, LW, RW, D)
    skaters_filter = {
        "players": {
            "filterSlotIds": {"value": [0,6,1,2,4]},  # Позиции полевых игроков
            "filterStatsForCurrentSeasonScoringPeriodId": {"value": [scoring_period_id]},
            "sortAppliedStatTotal": None,
            "sortAppliedStatTotalForScoringPeriodId": {
                "sortAsc": False,
                "sortPriority": 2,
                "value": scoring_period_id
            },
            "sortStatId": None,
            "sortStatIdForScoringPeriodId": None,
            "sortPercOwned": {
                "sortPriority": 3,
                "sortAsc": False
            },
            "limit": 50
        }
    }

    # Фильтр для вратарей
    goalies_filter = {
        "players": {
            "filterSlotIds": {"value": [5]},  # Позиция вратаря
            "filterStatsForCurrentSeasonScoringPeriodId": {"value": [scoring_period_id]},
            "sortPercOwned": {"sortPriority": 3, "sortAsc": False},
            "limit": 50,
            "sortAppliedStatTotalForScoringPeriodId": {
                "sortAsc": False,
                "sortPriority": 1,
                "value": scoring_period_id
            },
            "filterRanksForScoringPeriodIds": {"value": [scoring_period_id]},
            "filterRanksForRankTypes": {"value": ["STANDARD"]}
        }
    }

    url = API_URL_TEMPLATE.format(league_id=league_id)
    all_data = None

    # Запрос для полевых игроков
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            headers = base_headers.copy()
            headers['x-fantasy-filter'] = json.dumps(skaters_filter)
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            all_data = response.json()
            break
        except requests.exceptions.RequestException as e:
            logging.warning(f"Попытка {attempt} для полевых игроков не удалась: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                logging.error("Все попытки получить данные полевых игроков не удались")
                return None

    # Запрос для вратарей
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            headers = base_headers.copy()
            headers['x-fantasy-filter'] = json.dumps(goalies_filter)
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            goalies_data = response.json()
            
            # Добавляем вратарей к общим данным
            if all_data and 'players' in all_data and 'players' in goalies_data:
                all_data['players'].extend(goalies_data['players'])
            break
        except requests.exceptions.RequestException as e:
            logging.warning(f"Попытка {attempt} для вратарей не удалась: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                logging.error("Все попытки получить данные вратарей не удались")

    return all_data

def parse_player_data(data, scoring_period_id):
    """
    Парсит данные о игроках и распределяет их по позициям.
    """
    players_data = data.get('players', [])

    # Инициализируем списки для каждой позиции
    centers = []
    left_wings = []
    right_wings = []
    defensemen = []
    goalies = []

    for player_entry in players_data:
        player = player_entry.get('player', {})
        name = player.get('fullName', 'Unknown')
        position_id = player.get('defaultPositionId', -1)
        position = POSITION_MAP.get(position_id, 'Unknown')

        # Получаем очки appliedTotal за нужный период
        stats = player.get('stats', [])
        applied_total = 0
        for stat in stats:
            if stat.get('scoringPeriodId') == scoring_period_id:
                # Логируем содержимое stat для диагностики
                logging.debug(f"Player: {name}, Stat: {stat}")
                # Попробуем извлечь 'appliedTotal' или аналогичное поле
                applied_total = round(stat.get('appliedTotal', 0), 2)
                # Если 'appliedTotal' отсутствует, попробуем другие ключи
                if not applied_total:
                    applied_total = round(stat.get('value', 0), 2)
                if not applied_total:
                    applied_total = round(stat.get('total', 0), 2)
                break

        player_info = {
            'name': name,
            'position': position,
            'appliedTotal': applied_total
        }

        # Добавляем игрока в соответствующий список
        if position == 'C':
            centers.append(player_info)
        elif position == 'LW':
            left_wings.append(player_info)
        elif position == 'RW':
            right_wings.append(player_info)
        elif position == 'D':
            defensemen.append(player_info)
        elif position == 'G':
            goalies.append(player_info)

    logging.info(f"Парсинг данных завершён для scoringPeriodId {scoring_period_id}")
    return centers, left_wings, right_wings, defensemen, goalies

def select_top_players(players_list, top_n=1):
    """
    Выбирает топ N игроков из списка по appliedTotal.
    """
    return sorted(players_list, key=lambda x: x['appliedTotal'], reverse=True)[:top_n]

def assemble_team(centers, left_wings, right_wings, defensemen, goalies):
    """
    Составляет "команду дня" с уникальными позициями для нападающих.
    """
    top_center = select_top_players(centers, 1)
    top_lw = select_top_players(left_wings, 1)
    top_rw = select_top_players(right_wings, 1)
    top_defensemen = select_top_players(defensemen, 2)
    top_goalie = select_top_players(goalies, 1)

    team_of_the_day = {
        'C': top_center,
        'LW': top_lw,
        'RW': top_rw,
        'D': top_defensemen,
        'G': top_goalie
    }

    logging.info("Команда дня успешно собрана.")
    return team_of_the_day

async def display_team(team_of_the_day):
    """
    Формирует сообщение о "команде дня" и отправляет его в Telegram.
    """
    def get_player(position_players):
        return position_players[0] if position_players else None

    message = "<b>Команда дня:</b>\n\n<b>Нападающие:</b>\n"

    # Нападающие
    center = get_player(team_of_the_day['C'])
    lw = get_player(team_of_the_day['LW'])
    rw = get_player(team_of_the_day['RW'])

    if center:
        message += f"{center['name']} (C): {center['appliedTotal']} ftps\n"
    else:
        message += "Нет данных для Центра (C)\n"

    if lw:
        message += f"{lw['name']} (LW): {lw['appliedTotal']} ftps\n"
    else:
        message += "Нет данных для Левого нападающего (LW)\n"

    if rw:
        message += f"{rw['name']} (RW): {rw['appliedTotal']} ftps\n"
    else:
        message += "Нет данных для Правого нападающего (RW)\n"

    # Защитники
    message += "\n<b>Защитники:</b>\n"
    if team_of_the_day['D']:
        for d_player in team_of_the_day['D']:
            message += f"{d_player['name']} (D): {d_player['appliedTotal']} ftps\n"
    else:
        message += "Нет данных для Защитников (D)\n"

    # Вратарь
    message += "\n<b>Вратарь:</b>\n"
    goalie = get_player(team_of_the_day['G'])
    if goalie:
        message += f"{goalie['name']} (G): {goalie['appliedTotal']} ftps\n"
    else:
        message += "Нет данных для Вратаря (G)\n"

    # Отправка сообщения в Telegram
    await send_telegram_message(message)

async def main():
    # Текущая дата
    current_date = datetime.now()
    logging.info(f"Текущая дата: {current_date.strftime('%Y-%m-%d')}")

    # Вычисляем scoringPeriodId
    current_scoring_period_id = calculate_scoring_period_id(
        current_date, SEASON_START_DATE, SEASON_START_SCORING_PERIOD_ID)
    if current_scoring_period_id is None:
        logging.error("Невозможно вычислить current_scoring_period_id.")
        return

    # Начинаем с предыдущего периода
    scoring_period_id = current_scoring_period_id - 1
    max_attempts = 5  # Максимальное число попыток для поиска данных
    attempts = 0
    team_of_the_day = None

    while attempts < max_attempts and team_of_the_day is None:
        logging.info(f"Попытка получить данные для scoringPeriodId {scoring_period_id}")
        data = fetch_player_data(scoring_period_id, LEAGUE_ID)

        if data:
            centers, left_wings, right_wings, defensemen, goalies = parse_player_data(
                data, scoring_period_id)

            # Проверяем, есть ли данные для хотя бы одной позиции
            if centers or left_wings or right_wings or defensemen or goalies:
                team_of_the_day = assemble_team(
                    centers, left_wings, right_wings, defensemen, goalies)
                logging.info(f"Данные найдены для scoringPeriodId {scoring_period_id}")
            else:
                logging.warning(f"Нет данных для scoringPeriodId {scoring_period_id}. Переходим к предыдущему периоду.")
                scoring_period_id -= 1
        else:
            logging.warning(f"Нет данных для scoringPeriodId {scoring_period_id}. Переходим к предыдущему периоду.")
            scoring_period_id -= 1

        attempts += 1

    if team_of_the_day:
        await display_team(team_of_the_day)
    else:
        logging.error(f"Не удалось получить данные после {max_attempts} попыток.")
        await send_telegram_message("Команда дня не может быть сформирована из-за отсутствия данных.")

if __name__ == "__main__":
    asyncio.run(main())
