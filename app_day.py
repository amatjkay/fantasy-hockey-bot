import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
from datetime import datetime, timedelta
import logging
from telegram import Bot
from telegram.constants import ParseMode
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import os
import asyncio
import pytz
import time
import sys

# Конфигурация
LOG_FILE = "C:\\dev\\fantasy-hockey-bot\\log.txt"
ESPN_TIMEZONE = pytz.timezone('US/Eastern')  # Используем только время ESPN
SEASON_START_DATE = datetime(2024, 10, 4, tzinfo=ESPN_TIMEZONE)
SEASON_START_SCORING_PERIOD_ID = 1
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

# Настройка ретраев и таймаутов
retry_strategy = Retry(
    total=3,  # количество попыток
    backoff_factor=1,  # время между попытками будет увеличиваться
    status_forcelist=[429, 500, 502, 503, 504],  # коды ошибок для повторных попыток
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("https://", adapter)
session.mount("http://", adapter)

TIMEOUT = 10  # таймаут в секундах

# Логирование
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# Загрузка переменных окружения
load_dotenv('C:\\dev\\fantasy-hockey-bot\\.env')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

if not TELEGRAM_TOKEN or not CHAT_ID:
    logging.error("TELEGRAM_TOKEN или CHAT_ID не установлены в файле .env.")
    exit(1)

bot = Bot(token=TELEGRAM_TOKEN)

def get_current_week_dates():
    """Получение дат текущей недели по времени ESPN"""
    espn_now = datetime.now(ESPN_TIMEZONE)
    
    # Находим вторник текущей недели
    days_since_tuesday = (espn_now.weekday() - 1) % 7
    tuesday = espn_now - timedelta(days=days_since_tuesday)
    tuesday = tuesday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Находим следующий понедельник
    next_monday = tuesday + timedelta(days=6)
    next_monday = next_monday.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return tuesday, next_monday

def get_previous_week_dates():
    """Получение дат предыдущей недели по времени ESPN"""
    espn_now = datetime.now(ESPN_TIMEZONE)
    
    # Находим вторник текущей недели
    days_since_tuesday = (espn_now.weekday() - 1) % 7
    current_tuesday = espn_now - timedelta(days=days_since_tuesday)
    current_tuesday = current_tuesday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Получаем вторник предыдущей недели
    previous_tuesday = current_tuesday - timedelta(days=7)
    previous_monday = previous_tuesday + timedelta(days=6)
    previous_monday = previous_monday.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return previous_tuesday, previous_monday

def update_week_period():
    """Обновление периода недели и проверка на новую неделю"""
    tuesday, next_monday = get_current_week_dates()
    week_key = f"{tuesday.strftime('%Y-%m-%d')}_{next_monday.strftime('%Y-%m-%d')}"
    
    if os.path.exists(PLAYER_STATS_FILE):
        with open(PLAYER_STATS_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {"current_week": {}, "weeks": {}}

    # Проверяем, началась ли новая неделя
    if data.get("current_week", {}).get("start_date") != tuesday.strftime("%Y-%m-%d"):
        # Создаем структуру для новой недели
        if week_key not in data["weeks"]:
            data["weeks"][week_key] = {"players": {}}
        
        data["current_week"] = {
            "start_date": tuesday.strftime("%Y-%m-%d"),
            "end_date": next_monday.strftime("%Y-%m-%d")
        }
        
        with open(PLAYER_STATS_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    return tuesday, next_monday

def calculate_grade(team_of_the_day_count):
    """Определение грейда игрока на основе количества попаданий в команду недели"""
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

def update_player_stats(player_id, name, date_str, applied_total, team_of_the_day=False):
    """Обновление статистики игрока с учетом недельной статистики"""
    if os.path.exists(PLAYER_STATS_FILE):
        with open(PLAYER_STATS_FILE, 'r') as f:
            player_stats = json.load(f)
    else:
        player_stats = {"current_week": {}, "weeks": {}}

    # Определяем к какой неделе относится дата
    date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=ESPN_TIMEZONE)
    days_since_tuesday = (date.weekday() - 1) % 7
    week_start = date - timedelta(days=days_since_tuesday)
    week_end = week_start + timedelta(days=6)
    week_key = f"{week_start.strftime('%Y-%m-%d')}_{week_end.strftime('%Y-%m-%d')}"

    # Создаем структуру для недели, если её нет
    if week_key not in player_stats["weeks"]:
        player_stats["weeks"][week_key] = {"players": {}}

    week_stats = player_stats["weeks"][week_key]["players"]
    
    if str(player_id) not in week_stats:
        week_stats[str(player_id)] = {
            "name": name,
            "team_of_the_day_count": 0,
            "grade": "common",
            "team_of_the_day_dates": []
        }

    stats = week_stats[str(player_id)]
    stats["name"] = name

    # Проверяем уникальность даты перед добавлением
    if team_of_the_day and date_str not in stats["team_of_the_day_dates"]:
        stats["team_of_the_day_dates"].append(date_str)
        stats["team_of_the_day_count"] = len(stats["team_of_the_day_dates"])
        stats["grade"] = calculate_grade(stats["team_of_the_day_count"])
        logging.info(f"Обновление грейда для игрока {name}: {stats['grade']} ({stats['team_of_the_day_count']} раз)")

    # Обновляем информацию о текущей неделе
    current_date = datetime.now(ESPN_TIMEZONE)
    current_days_since_tuesday = (current_date.weekday() - 1) % 7
    current_week_start = current_date - timedelta(days=current_days_since_tuesday)
    current_week_end = current_week_start + timedelta(days=6)
    
    player_stats["current_week"] = {
        "start_date": current_week_start.strftime("%Y-%m-%d"),
        "end_date": current_week_end.strftime("%Y-%m-%d")
    }

    with open(PLAYER_STATS_FILE, 'w') as f:
        json.dump(player_stats, f, indent=4)
    
    return stats["grade"]

def fetch_player_data(scoring_period_id, league_id, max_retries=3, timeout=10):
    """Получение данных игроков из API ESPN с поддержкой повторных попыток"""
    base_headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0',
    }

    filters = {
        "players": {
            "filterSlotIds": {"value": [0, 6, 1, 2, 4, 5]},
            "filterStatsForCurrentSeasonScoringPeriodId": {"value": [scoring_period_id]},
            "sortAppliedStatTotalForScoringPeriodId": {"sortAsc": False, "sortPriority": 2, "value": scoring_period_id},
            "limit": 100
        }
    }

    url = API_URL_TEMPLATE.format(league_id=league_id)
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logging.info(f"Запрос данных для scoring_period_id={scoring_period_id} (попытка {retry_count + 1}/{max_retries})")
            headers = base_headers.copy()
            headers['x-fantasy-filter'] = json.dumps(filters)
            response = session.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            if not data.get('players'):
                raise ValueError("Получен пустой список игроков")
            logging.info(f"Успешно получены данные для scoring_period_id={scoring_period_id}")
            return data
        except requests.exceptions.Timeout:
            retry_count += 1
            logging.warning(f"Таймаут при запросе данных (попытка {retry_count}/{max_retries})")
            if retry_count == max_retries:
                logging.error("Превышено максимальное количество попыток из-за таймаута")
                return None
            time.sleep(2 * retry_count)  # Увеличиваем время ожидания с каждой попыткой
        except requests.exceptions.RequestException as e:
            retry_count += 1
            logging.warning(f"Ошибка при запросе данных: {str(e)} (попытка {retry_count}/{max_retries})")
            if retry_count == max_retries:
                logging.error(f"Превышено максимальное количество попыток: {str(e)}")
                return None
            time.sleep(2 * retry_count)
        except ValueError as e:
            logging.error(f"Ошибка в данных: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Неожиданная ошибка: {str(e)}")
            return None

def parse_player_data(data, scoring_period_id, target_date):
    """Разбор данных игроков с учетом недельной статистики"""
    players_data = data.get('players', [])
    positions = {'C': [], 'LW': [], 'RW': [], 'D': [], 'G': []}

    try:
        with open(PLAYER_STATS_FILE, 'r') as f:
            player_stats = json.load(f)
            
        # Определяем неделю для целевой даты
        days_since_tuesday = (target_date.weekday() - 1) % 7
        week_start = target_date - timedelta(days=days_since_tuesday)
        week_end = week_start + timedelta(days=6)
        week_key = f"{week_start.strftime('%Y-%m-%d')}_{week_end.strftime('%Y-%m-%d')}"
        
        week_stats = player_stats.get("weeks", {}).get(week_key, {}).get("players", {})
    except Exception as e:
        logging.warning(f"Ошибка при загрузке файла статистики игроков: {e}")
        week_stats = {}

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
                'grade': week_stats.get(player_id, {}).get("grade", "common")
            })

    return positions

def create_collage(team, date_str):
    """Создание коллажа с учетом грейдов игроков"""
    player_img_width, player_img_height = 130, 100
    padding = 20
    text_padding = 10
    line_height = player_img_height + text_padding + 30 + padding

    total_players = sum(len(players) for players in team.values())
    height = total_players * line_height + padding * 2
    width = 500

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    font_path = "C:\\Windows\\Fonts\\arial.ttf"
    font = ImageFont.truetype(font_path, size=20)

    y_offset = padding
    
    # Добавляем заголовок с датой
    title = f"Команда дня {date_str}"
    title_width = draw.textlength(title, font=font)
    draw.text(((width - title_width) // 2, y_offset), title, fill="black", font=font)
    y_offset += 40

    for position, players in team.items():
        for player in players:
            name = player['name']
            points = player['appliedTotal']
            image_url = player['image_url']
            grade = player['grade']
            color = GRADE_COLORS.get(grade, "black")

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

async def send_collage(team, date_str):
    """Отправка коллажа команды дня в Telegram"""
    try:
        # Создание коллажа
        image = create_collage(team)
        
        # Сохранение коллажа во временный файл
        temp_file = f"collage_{date_str}.jpg"
        image.save(temp_file)
        
        # Формирование текста сообщения
        message = f"Команда дня {date_str}:\n\n"
        for position, players in team.items():
            for player in players:
                grade_emoji = GRADE_EMOJI.get(player['grade'], '')
                message += f"{position}: {player['name']} ({player['appliedTotal']:.2f} ftps) {grade_emoji}\n"
        
        # Отправка коллажа
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                with open(temp_file, 'rb') as photo:
                    await bot.send_photo(chat_id=CHAT_ID, photo=photo, caption=message, parse_mode=ParseMode.HTML)
                logging.info(f"Коллаж успешно отправлен для даты {date_str}")
                break
            except Exception as e:
                if attempt < max_attempts:
                    logging.warning(f"Попытка {attempt} из {max_attempts} не удалась: {str(e)}")
                    await asyncio.sleep(1)
                else:
                    logging.error(f"Ошибка при отправке коллажа после {max_attempts} попыток: {str(e)}")
                    # Отправляем только текст, если не удалось отправить коллаж
                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=ParseMode.HTML)
        
        # Удаление временного файла
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
    except Exception as e:
        logging.error(f"Ошибка при создании/отправке коллажа: {str(e)}")
        # В случае ошибки отправляем только текст
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=ParseMode.HTML)

async def send_text_message(team, date_str):
    """Отправка текстового сообщения при ошибке с коллажем"""
    try:
        message = f"\U0001F3D2 Команда дня {date_str}\n\n"
        for position, players in team.items():
            for player in players:
                message += f"{position}: {player['name']} ({player['appliedTotal']:.2f} ftps)\n"
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=ParseMode.HTML)
        logging.info(f"Текстовое сообщение успешно отправлено для даты {date_str}")
    except Exception as e:
        logging.error(f"Не удалось отправить даже текстовое сообщение: {str(e)}")

async def process_dates_range(start_date, end_date):
    """Обработка данных за указанный диапазон дат"""
    current_date = start_date
    while current_date <= min(datetime.now(ESPN_TIMEZONE), end_date):
        try:
            logging.info(f"=== Начало обработки даты: {current_date.strftime('%Y-%m-%d')} ===")
            
            scoring_period_id = (current_date.date() - SEASON_START_DATE.date()).days + SEASON_START_SCORING_PERIOD_ID
            logging.info(f"Расчетный scoring_period_id: {scoring_period_id}")

            data = fetch_player_data(scoring_period_id - 1, LEAGUE_ID)
            if not data:
                logging.error(f"Пропуск даты {current_date.strftime('%Y-%m-%d')} из-за ошибки получения данных")
                current_date += timedelta(days=1)
                continue

            positions = parse_player_data(data, scoring_period_id - 1, current_date)
            team = {
                'C': sorted(positions['C'], key=lambda x: x['appliedTotal'], reverse=True)[:1],
                'LW': sorted(positions['LW'], key=lambda x: x['appliedTotal'], reverse=True)[:1],
                'RW': sorted(positions['RW'], key=lambda x: x['appliedTotal'], reverse=True)[:1],
                'D': sorted(positions['D'], key=lambda x: x['appliedTotal'], reverse=True)[:2],
                'G': sorted(positions['G'], key=lambda x: x['appliedTotal'], reverse=True)[:1]
            }

            date_str = current_date.strftime("%Y-%m-%d")
            
            # Логируем состав команды
            logging.info(f"Состав команды дня {date_str}:")
            for position, players in team.items():
                for player in players:
                    logging.info(f"{position}: {player['name']} ({player['appliedTotal']:.2f} ftps)")

            for position, players in team.items():
                for player in players:
                    if player['appliedTotal'] > 0:
                        grade = update_player_stats(
                            player_id=player['id'],
                            name=player['name'],
                            date_str=date_str,
                            applied_total=player['appliedTotal'],
                            team_of_the_day=True
                        )
                        player['grade'] = grade

            await send_collage(team, date_str)
            logging.info(f"=== Завершена обработка даты: {date_str} ===\n")

            # Пауза между датами
            await asyncio.sleep(2)

            current_date += timedelta(days=1)
            current_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
        except Exception as e:
            logging.error(f"Критическая ошибка при обработке даты {current_date.strftime('%Y-%m-%d')}: {str(e)}")
            current_date += timedelta(days=1)
            continue

def get_all_weeks_dates():
    """Получение списка всех недель с начала сезона"""
    weeks = []
    current_date = SEASON_START_DATE
    
    # Находим первый вторник после начала сезона
    days_until_tuesday = (1 - current_date.weekday()) % 7  # 1 = вторник
    first_tuesday = current_date + timedelta(days=days_until_tuesday)
    first_tuesday = first_tuesday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Получаем текущий вторник
    now = datetime.now(ESPN_TIMEZONE)
    days_since_tuesday = (now.weekday() - 1) % 7
    current_tuesday = now - timedelta(days=days_since_tuesday)
    current_tuesday = current_tuesday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Генерируем все недели
    week_start = first_tuesday
    while week_start <= current_tuesday:
        week_end = week_start + timedelta(days=6)
        week_end = week_end.replace(hour=23, minute=59, second=59, microsecond=999999)
        weeks.append((week_start, week_end))
        week_start = week_start + timedelta(days=7)
    
    return weeks

async def main():
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--previous-week':
            # Обработка предыдущей недели
            previous_tuesday, previous_monday = get_previous_week_dates()
            logging.info(f"Обработка данных за предыдущую неделю: {previous_tuesday.strftime('%Y-%m-%d')} - {previous_monday.strftime('%Y-%m-%d')}")
            await process_dates_range(previous_tuesday, previous_monday)
        elif sys.argv[1] == '--all-weeks':
            # Обработка всех недель с начала сезона
            weeks = get_all_weeks_dates()
            total_weeks = len(weeks)
            
            logging.info(f"Начинаем обработку всех недель с начала сезона ({total_weeks} недель)")
            for i, (week_start, week_end) in enumerate(weeks, 1):
                logging.info(f"Обработка недели {i}/{total_weeks}: {week_start.strftime('%Y-%m-%d')} - {week_end.strftime('%Y-%m-%d')}")
                await process_dates_range(week_start, week_end)
                # Небольшая пауза между неделями чтобы не перегружать API
                if i < total_weeks:
                    await asyncio.sleep(2)
    else:
        # Обработка текущей недели
        tuesday, next_monday = update_week_period()
        logging.info(f"Обработка данных за текущую неделю: {tuesday.strftime('%Y-%m-%d')} - {next_monday.strftime('%Y-%m-%d')}")
        await process_dates_range(tuesday, next_monday)

if __name__ == "__main__":
    asyncio.run(main())
