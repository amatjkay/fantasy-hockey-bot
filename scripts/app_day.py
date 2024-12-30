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
import traceback
from pathlib import Path
import argparse

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Конфигурация
LOG_FILE = "logs/app/log.txt"
ESPN_TIMEZONE = pytz.timezone('US/Eastern')  # Используем только время ESPN
SEASON_START_DATE = datetime(2024, 10, 4, tzinfo=ESPN_TIMEZONE)
SEASON_START_SCORING_PERIOD_ID = 1
LEAGUE_ID = 484910394
API_URL_TEMPLATE = 'https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/2025/segments/0/leagues/{league_id}?view=kona_player_info'
PLAYER_STATS_FILE = "data/processed/player_stats.json"

POSITION_MAP = {
    1: 'C',
    2: 'LW',
    3: 'RW',
    4: 'D',
    5: 'G'
}

GRADE_COLORS = {
    "common": "black",     # обычный
    "uncommon": "green",   # необычный
    "rare": "blue",        # редкий
    "epic": "purple",      # эпический
    "legend": "orange"     # легендарный
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

TIMEOUT = 30  # таймаут в секундах

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  # Добавляем вывод в консоль
    ]
)

# Загрузка переменных окружения
load_dotenv('.env')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

if not TELEGRAM_TOKEN or not CHAT_ID:
    logging.error("TELEGRAM_TOKEN или CHAT_ID не установлены в файле .env.")
    exit(1)

logging.info("Инициализация бота...")
bot = Bot(token=TELEGRAM_TOKEN)
logging.info("Бот успешно инициализирован")

def get_current_week_dates():
    """Получение дат текущей недели по времени ESPN"""
    espn_now = datetime.now(ESPN_TIMEZONE)
    day_start_hour = int(os.getenv('DAY_START_HOUR', '4'))
    
    # Корректируем дату, если время меньше 4 утра
    if espn_now.hour < day_start_hour:
        espn_now = espn_now - timedelta(days=1)
    
    # Находим понедельник текущей недели
    days_since_monday = espn_now.weekday()
    monday = espn_now - timedelta(days=days_since_monday)
    monday = monday.replace(hour=day_start_hour, minute=0, second=0, microsecond=0)
    
    # Находим следующее воскресенье
    sunday = monday + timedelta(days=6)
    sunday = sunday.replace(hour=day_start_hour-1, minute=59, second=59, microsecond=999999)
    
    return monday, sunday

def get_previous_week_dates():
    """Получение дат предыдущей недели по времени ESPN"""
    espn_now = datetime.now(ESPN_TIMEZONE)
    day_start_hour = int(os.getenv('DAY_START_HOUR', '4'))
    
    # Корректируем дату, если время меньше 4 утра
    if espn_now.hour < day_start_hour:
        espn_now = espn_now - timedelta(days=1)
    
    # Находим понедельник текущей недели
    days_since_monday = espn_now.weekday()
    current_monday = espn_now - timedelta(days=days_since_monday)
    current_monday = current_monday.replace(hour=day_start_hour, minute=0, second=0, microsecond=0)
    
    # Получаем понедельник предыдущей недели
    previous_monday = current_monday - timedelta(days=7)
    previous_sunday = previous_monday + timedelta(days=6)
    previous_sunday = previous_sunday.replace(hour=day_start_hour-1, minute=59, second=59, microsecond=999999)
    
    return previous_monday, previous_sunday

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

def update_player_stats(player_id, name, date_str, applied_total, position, team_of_the_day=False):
    """Обновление статистики игрока с учетом недельной статистики"""
    try:
        logging.info(f"Обновление статистики для игрока {name} (ID: {player_id})")
        logging.info(f"Дата: {date_str}, Позиция: {position}, Очки: {applied_total}")
        
        if os.path.exists(PLAYER_STATS_FILE):
            with open(PLAYER_STATS_FILE, 'r') as f:
                player_stats = json.load(f)
        else:
            player_stats = {
                "current_week": {},
                "weeks": {},
                "league_settings": {
                    "name": "",
                    "scoring": {},
                    "roster": {}
                }
            }

        # Определяем к какой неделе относится дата
        date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=ESPN_TIMEZONE)
        day_start_hour = int(os.getenv('DAY_START_HOUR', '4'))
        
        # Корректируем дату, если время меньше 4 утра
        if date.hour < day_start_hour:
            date = date - timedelta(days=1)
            
        # Находим понедельник текущей недели
        days_since_monday = date.weekday()
        week_start = date - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=day_start_hour, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=6)
        week_end = week_end.replace(hour=day_start_hour-1, minute=59, second=59, microsecond=999999)
        week_key = f"{week_start.strftime('%Y-%m-%d')}_{week_end.strftime('%Y-%m-%d')}"
        
        logging.info(f"Неделя: {week_key}")

        # Создаем структуру для недели, если её нет
        if week_key not in player_stats["weeks"]:
            player_stats["weeks"][week_key] = {"players": {}}

        week_stats = player_stats["weeks"][week_key]["players"]
        
        # Создаем или получаем запись игрока для текущей недели
        if str(player_id) not in week_stats:
            week_stats[str(player_id)] = {
                "name": name,
                "team_of_the_day_count": 0,
                "grade": "common",
                "team_of_the_day_dates": [],
                "positions": [],
                "daily_stats": {},
                "total_points": 0,
                "position_appearances": {}
            }

        stats = week_stats[str(player_id)]
        stats["name"] = name

        # Обновляем позиции
        if position not in stats["positions"]:
            stats["positions"].append(position)

        # Обновляем счетчик появлений для позиции
        if position not in stats["position_appearances"]:
            stats["position_appearances"][position] = 0
        stats["position_appearances"][position] += 1

        # Обновляем статистику за день
        stats["daily_stats"][date_str] = {
            "points": applied_total,
            "position": position,
            "team_of_the_day": team_of_the_day,
            "collage_sent": False
        }

        # Обновляем общее количество очков
        stats["total_points"] = sum(day["points"] for day in stats["daily_stats"].values())

        # Обновляем даты появления в команде дня и грейд
        if team_of_the_day:
            if date_str not in stats["team_of_the_day_dates"]:
                stats["team_of_the_day_dates"].append(date_str)
                stats["team_of_the_day_dates"].sort()
                stats["team_of_the_day_count"] = len(stats["team_of_the_day_dates"])
                stats["grade"] = calculate_grade(stats["team_of_the_day_count"])
                logging.info(f"Обновление грейда для игрока {name}: {stats['grade']} ({stats['team_of_the_day_count']} раз)")
                logging.info(f"Даты попадания в команду дня: {', '.join(stats['team_of_the_day_dates'])}")

        # Обновляем информацию о текущей неделе
        current_date = datetime.now(ESPN_TIMEZONE)
        if current_date.hour < day_start_hour:
            current_date = current_date - timedelta(days=1)
            
        current_days_since_monday = current_date.weekday()
        current_week_start = current_date - timedelta(days=current_days_since_monday)
        current_week_start = current_week_start.replace(hour=day_start_hour, minute=0, second=0, microsecond=0)
        current_week_end = current_week_start + timedelta(days=6)
        current_week_end = current_week_end.replace(hour=day_start_hour-1, minute=59, second=59, microsecond=999999)
        
        player_stats["current_week"] = {
            "start_date": current_week_start.strftime("%Y-%m-%d"),
            "end_date": current_week_end.strftime("%Y-%m-%d")
        }

        # Сохраняем обновленные данные
        with open(PLAYER_STATS_FILE, 'w') as f:
            json.dump(player_stats, f, indent=4)
        logging.info(f"Данные успешно сохранены в {PLAYER_STATS_FILE}")
        
        return stats.get("grade", "common")
    except Exception as e:
        logging.error(f"Ошибка при обновлении статистики игрока {name}: {str(e)}")
        traceback.print_exc()
        return "common"

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
        except requests.exceptions.ConnectionError as e:
            if "NameResolutionError" in str(e):
                retry_count += 1
                wait_time = min(8, 2 ** (retry_count - 1))  # 2, 4, 8 секунд
                logging.warning(f"Ошибка разрешения имени при запросе данных (попытка {retry_count}/3). Ожидание {wait_time} сек...")
                if retry_count == 3:
                    logging.error("Превышено максимальное количество попыток из-за ошибки разрешения имени")
                    return None
                time.sleep(wait_time)
            else:
                raise e
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
        days_since_monday = (target_date.weekday() - 1) % 7
        week_start = target_date - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        week_key = f"{week_start.strftime('%Y-%m-%d')}_{week_end.strftime('%Y-%m-%d')}"
        
        week_stats = player_stats.get("weeks", {}).get(week_key, {}).get("players", {})
    except Exception as e:
        logging.warning(f"Ошибка при загрузке файла статистики игроков: {e}")
        week_stats = {}

    for player_entry in players_data:
        try:
            player = player_entry.get('player', {})
            if not player:
                continue

            player_id = str(player.get('id'))
            if not player_id or player_id == 'unknown':
                continue

            name = player.get('fullName')
            if not name or name == 'Unknown':
                continue

            position_id = player.get('defaultPositionId')
            if not position_id or position_id == -1:
                continue

            position = POSITION_MAP.get(position_id)
            if not position:
                continue

            # Проверяем статистику игрока
            applied_total = 0
            valid_stats = False
            for stat in player.get('stats', []):
                if stat.get('scoringPeriodId') == scoring_period_id:
                    # Проверяем, что статистика относится к нужной дате
                    stat_date = stat.get('date')
                    if stat_date:
                        stat_date = datetime.strptime(stat_date, "%Y-%m-%d").replace(tzinfo=ESPN_TIMEZONE)
                        if stat_date.date() != target_date.date():
                            logging.warning(f"Статистика игрока {name} относится к другой дате: {stat_date.strftime('%Y-%m-%d')}, ожидалась: {target_date.strftime('%Y-%m-%d')}")
                            continue
                    
                    applied_total = round(stat.get('appliedTotal', 0), 2)
                    if applied_total > 0:  # Учитываем только положительные очки
                        valid_stats = True
                    break

            if not valid_stats:
                continue

            image_url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/nhl/players/full/{player_id}.png&w=130&h=100"

            if position in positions:
                positions[position].append({
                    'id': player_id,
                    'name': name,
                    'appliedTotal': applied_total,
                    'image_url': image_url,
                    'grade': week_stats.get(player_id, {}).get("grade", "common")
                })

        except Exception as e:
            logging.error(f"Ошибка при обработке данных игрока: {str(e)}")
            continue

    # Проверяем, что у нас есть хотя бы один игрок на каждой позиции
    empty_positions = [pos for pos, players in positions.items() if not players]
    if empty_positions:
        logging.warning(f"Нет игроков на позициях: {empty_positions}")

    return positions

def create_collage(team, date_str):
    """Создание коллажа с учетом грейдов игроков"""
    # Создаем директорию для кэша если её нет
    cache_dir = "data/cache/player_images"
    os.makedirs(cache_dir, exist_ok=True)
    
    player_img_width, player_img_height = 130, 100
    padding = 20
    text_padding = 10
    line_height = player_img_height + text_padding + 30 + padding

    total_players = sum(len(players) for players in team.values())
    height = total_players * line_height + padding * 2
    width = 500

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    # Поиск доступного шрифта в системе
    try:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf"
        ]
        
        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, size=20)
                logging.info(f"Используется шрифт: {font_path}")
                break
        
        if font is None:
            font = ImageFont.load_default()
            logging.warning("Используется дефолтный шрифт, так как не найдены системные шрифты")
    except Exception as e:
        logging.error(f"Ошибка при загрузке шрифта: {str(e)}")
        font = ImageFont.load_default()

    y_offset = padding
    
    # Добавляем заголовок с датой
    title = f"Команда дня {date_str}"
    try:
        title_width = draw.textlength(title, font=font)
    except AttributeError:
        title_width = font.getlength(title)
    draw.text(((width - title_width) // 2, y_offset), title, fill="black", font=font)
    y_offset += 40

    for position, players in team.items():
        for player in players:
            name = player['name']
            points = player['appliedTotal']
            image_url = player['image_url']
            grade = player['grade']
            color = GRADE_COLORS.get(grade, "black")

            # Проверяем кэш
            player_id = player['id']
            cache_file = os.path.join(cache_dir, f"{player_id}.jpg")
            
            if os.path.exists(cache_file):
                try:
                    player_image = Image.open(cache_file).convert("RGB")
                    logging.info(f"Изображение для {name} загружено из кэша")
                except Exception as e:
                    logging.warning(f"Ошибка загрузки из кэша для {name}: {e}")
                    os.remove(cache_file)  # Удаляем поврежденный файл
                    player_image = None
            else:
                player_image = None

            if player_image is None:
                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        response = requests.get(image_url, stream=True, timeout=30)
                        response.raise_for_status()
                        player_image = Image.open(response.raw).convert("RGBA")
                        bg = Image.new("RGBA", player_image.size, (255, 255, 255, 255))
                        combined_image = Image.alpha_composite(bg, player_image)
                        player_image = combined_image.convert("RGB")
                        
                        # Сохраняем в кэш
                        player_image.save(cache_file)
                        logging.info(f"Изображение для {name} успешно загружено и сохранено в кэш (попытка {retry_count + 1})")
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            logging.warning(f"Ошибка загрузки изображения для {name} (попытка {retry_count}/{max_retries}): {e}")
                            time.sleep(2 ** retry_count)  # Экспоненциальная задержка
                        else:
                            logging.error(f"Не удалось загрузить изображение для {name} после {max_retries} попыток: {e}")
                            player_image = Image.new("RGB", (player_img_width, player_img_height), "gray")

            # Изменяем размер изображения
            player_image = player_image.resize((player_img_width, player_img_height), Image.LANCZOS)
            image_x = (width - player_img_width) // 2
            image.paste(player_image, (image_x, y_offset))

            text = f"{position}: {name} ({points:.2f} ftps)"
            try:
                text_width = draw.textlength(text, font=font)
            except AttributeError:
                text_width = font.getlength(text)
            text_x = (width - text_width) // 2
            draw.text((text_x, y_offset + player_img_height + text_padding), text, fill=color, font=font)
            y_offset += line_height

    file_path = f"team_day_collage_{date_str}.jpg"
    image.save(file_path)
    return file_path

async def send_collage(team, date_str):
    """Отправка коллажа команды дня в Telegram"""
    try:
        # Проверяем, был ли уже отправлен коллаж за эту дату
        if os.path.exists(PLAYER_STATS_FILE):
            with open(PLAYER_STATS_FILE, 'r') as f:
                data = json.load(f)
                for week_key, week_data in data.get("weeks", {}).items():
                    for player_id, player_data in week_data.get("players", {}).items():
                        if date_str in player_data.get("daily_stats", {}) and player_data["daily_stats"][date_str].get("collage_sent", False):
                            logging.info(f"Коллаж для даты {date_str} уже был отправлен ранее, пропускаем")
                            return

        # Создание коллажа
        file_path = create_collage(team, date_str)
        
        # Отправка коллажа
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                with open(file_path, 'rb') as photo:
                    await bot.send_photo(chat_id=CHAT_ID, photo=photo, parse_mode=ParseMode.HTML)
                logging.info(f"Коллаж успешно отправлен для даты {date_str}")
                
                # Отмечаем, что коллаж был отправлен
                if os.path.exists(PLAYER_STATS_FILE):
                    with open(PLAYER_STATS_FILE, 'r') as f:
                        data = json.load(f)
                    
                    # Находим нужную неделю и обновляем статус отправки коллажа
                    for week_key, week_data in data.get("weeks", {}).items():
                        for player_id, player_data in week_data.get("players", {}).items():
                            if date_str in player_data.get("daily_stats", {}):
                                player_data["daily_stats"][date_str]["collage_sent"] = True
                    
                    with open(PLAYER_STATS_FILE, 'w') as f:
                        json.dump(data, f, indent=4)
                
                break
            except Exception as e:
                if attempt < max_attempts:
                    logging.warning(f"Попытка {attempt} из {max_attempts} не удалась: {str(e)}")
                    await asyncio.sleep(1)
                else:
                    logging.error(f"Не удалось отправить коллаж после {max_attempts} попыток: {str(e)}")
        
        # Удаление временного файла
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        logging.error(f"Ошибка при создании/отправке коллажа: {str(e)}")

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

async def process_dates_range(start_date, end_date, force=False):
    """Обработка данных за указанный диапазон дат"""
    current_date = start_date
    # Считаем количество дней включительно: конец - начало + 1
    total_days = (end_date - start_date).days + 1
    processed_days = 0
    
    logging.info(f"Начинаем обработку периода с {start_date.strftime('%Y-%m-%d')} по {end_date.strftime('%Y-%m-%d')}")
    logging.info(f"Всего дней для обработки: {total_days} (с {start_date.strftime('%A')} по {end_date.strftime('%A')})")
    
    while current_date <= min(datetime.now(ESPN_TIMEZONE), end_date):
        try:
            processed_days += 1
            date_str = current_date.strftime('%Y-%m-%d')
            day_name = current_date.strftime('%A')
            logging.info(f"=== Обработка дня {processed_days}/{total_days}: {date_str} ({day_name}) ===")
            
            # Проверяем, был ли уже отправлен коллаж за эту дату
            if not force and os.path.exists(PLAYER_STATS_FILE):
                with open(PLAYER_STATS_FILE, 'r') as f:
                    data = json.load(f)
                    skip_date = False
                    for week_data in data.get("weeks", {}).values():
                        for player_data in week_data.get("players", {}).values():
                            if date_str in player_data.get("daily_stats", {}) and \
                               player_data["daily_stats"][date_str].get("collage_sent", False):
                                logging.info(f"Пропуск даты {date_str} - коллаж уже был отправлен (используйте --force для повторной отправки)")
                                skip_date = True
                                break
                        if skip_date:
                            break
                    if skip_date:
                        current_date += timedelta(days=1)
                        continue

            # Учитываем время начала дня при расчете scoring_period_id
            day_start_hour = int(os.getenv('DAY_START_HOUR', '4'))
            adjusted_date = current_date
            if current_date.hour < day_start_hour:
                adjusted_date = current_date - timedelta(days=1)
            
            scoring_period_id = (adjusted_date.date() - SEASON_START_DATE.date()).days + SEASON_START_SCORING_PERIOD_ID
            logging.info(f"Запрашиваем данные для scoring_period_id: {scoring_period_id}")

            data = fetch_player_data(scoring_period_id, LEAGUE_ID)
            if not data:
                logging.error(f"Пропуск даты {date_str} - не удалось получить данные")
                current_date += timedelta(days=1)
                continue

            # Проверяем, что данные относятся к нужной дате
            game_date = data.get('gameDate')
            if game_date:
                game_date = datetime.strptime(game_date, "%Y-%m-%d").replace(tzinfo=ESPN_TIMEZONE)
                if game_date.date() != adjusted_date.date():
                    logging.warning(f"Данные относятся к другой дате: {game_date.strftime('%Y-%m-%d')}, ожидалась: {adjusted_date.strftime('%Y-%m-%d')}")
                    current_date += timedelta(days=1)
                    continue

            logging.info(f"Обрабатываем статистику игроков за {date_str}")
            positions = parse_player_data(data, scoring_period_id, adjusted_date)
            
            # Проверяем наличие игроков на каждой позиции
            empty_positions = [pos for pos, players in positions.items() if not players]
            if empty_positions:
                logging.warning(f"Нет игроков на позициях: {', '.join(empty_positions)}")
                if len(empty_positions) == len(positions):
                    logging.info(f"Пропуск даты {date_str} - нет игр")
                    current_date += timedelta(days=1)
                    continue
            
            team = {
                'C': sorted(positions['C'], key=lambda x: x['appliedTotal'], reverse=True)[:1],
                'LW': sorted(positions['LW'], key=lambda x: x['appliedTotal'], reverse=True)[:1],
                'RW': sorted(positions['RW'], key=lambda x: x['appliedTotal'], reverse=True)[:1],
                'D': sorted(positions['D'], key=lambda x: x['appliedTotal'], reverse=True)[:2],
                'G': sorted(positions['G'], key=lambda x: x['appliedTotal'], reverse=True)[:1]
            }

            # Проверяем, есть ли хотя бы один игрок в команде
            has_players = any(players for players in team.values())
            if not has_players:
                logging.info(f"Пропуск даты {date_str} - нет игроков для команды дня")
                current_date += timedelta(days=1)
                continue

            # Логируем состав команды
            logging.info(f"Состав команды дня {date_str}:")
            for position, players in team.items():
                for player in players:
                    logging.info(f"{position}: {player['name']} ({player['appliedTotal']:.2f} ftps)")
                    # Обновляем статистику игрока
                    grade = update_player_stats(
                        player_id=player['id'],
                        name=player['name'],
                        date_str=date_str,
                        applied_total=player['appliedTotal'],
                        position=position,
                        team_of_the_day=True
                    )
                    player['grade'] = grade

            # Отправляем коллаж
            logging.info(f"Отправка коллажа для даты {date_str}")
            try:
                await send_collage(team, date_str)
            except Exception as e:
                logging.error(f"Ошибка при отправке коллажа: {str(e)}")
                logging.info("Пробуем отправить текстовое сообщение...")
                await send_text_message(team, date_str)

            logging.info(f"=== Завершена обработка даты: {date_str} ===\n")

            # Пауза между датами
            await asyncio.sleep(2)

            current_date += timedelta(days=1)
            
        except Exception as e:
            logging.error(f"Критическая ошибка при обработке даты {current_date.strftime('%Y-%m-%d')}: {str(e)}")
            logging.error(traceback.format_exc())
            current_date += timedelta(days=1)
            continue
    
    logging.info(f"Завершена обработка периода. Обработано дней: {processed_days}")

def get_all_weeks_dates():
    """Получение списка всех недель с начала сезона"""
    weeks = []
    current_date = SEASON_START_DATE
    day_start_hour = int(os.getenv('DAY_START_HOUR', '4'))
    
    # Находим первый понедельник после начала сезона
    days_until_monday = (0 - current_date.weekday()) % 7  # 0 = понедельник
    first_monday = current_date + timedelta(days=days_until_monday)
    first_monday = first_monday.replace(hour=day_start_hour, minute=0, second=0, microsecond=0)
    
    # Получаем текущую дату
    now = datetime.now(ESPN_TIMEZONE)
    if now.hour < day_start_hour:
        now = now - timedelta(days=1)
    
    # Находим конец текущей недели (воскресенье)
    days_until_sunday = 6 - now.weekday()  # 6 = воскресенье
    current_sunday = now + timedelta(days=days_until_sunday)
    current_sunday = current_sunday.replace(hour=day_start_hour-1, minute=59, second=59, microsecond=999999)
    
    # Генерируем все недели
    week_start = first_monday
    while week_start <= current_sunday:
        # Конец недели - это воскресенье (через 6 дней после понедельника)
        week_end = week_start + timedelta(days=6)
        week_end = week_end.replace(hour=day_start_hour-1, minute=59, second=59, microsecond=999999)
        # Если это последняя неделя, ограничиваем конец текущей датой
        if week_end > current_sunday:
            week_end = current_sunday
        weeks.append((week_start, week_end))
        # Следующая неделя начинается через 7 дней
        week_start = week_start + timedelta(days=7)
    
    return weeks

async def main():
    try:
        # Создаем парсер аргументов
        parser = argparse.ArgumentParser(description='Скрипт для создания команды дня')
        parser.add_argument('--all-weeks', action='store_true', help='Обработать все недели с начала сезона')
        parser.add_argument('--force', action='store_true', help='Принудительная обработка всех дней, даже если они уже были обработаны')
        parser.add_argument('--date', help='Обработать конкретную дату в формате YYYY-MM-DD')
        args = parser.parse_args()

        # Если используется --force, очищаем файл статистики
        if args.force and os.path.exists(PLAYER_STATS_FILE):
            logging.info("Очищаем существующую статистику из-за флага --force")
            with open(PLAYER_STATS_FILE, 'w') as f:
                json.dump({"current_week": {}, "weeks": {}}, f, indent=4)

        if args.date:
            # Обработка конкретной даты
            try:
                target_date = datetime.strptime(args.date, '%Y-%m-%d')
                target_date = target_date.replace(hour=int(os.getenv('DAY_START_HOUR', '4')), 
                                               minute=0, second=0, microsecond=0,
                                               tzinfo=ESPN_TIMEZONE)
                logging.info(f"Обработка данных за указанную дату: {args.date}")
                await process_dates_range(target_date, target_date, force=True)
            except ValueError:
                logging.error("Неверный формат даты. Используйте YYYY-MM-DD")
                sys.exit(1)
        elif args.all_weeks:
            # Обработка всех недель с начала сезона
            weeks = get_all_weeks_dates()
            total_weeks = len(weeks)
            
            logging.info(f"Начинаем обработку всех недель с начала сезона ({total_weeks} недель)")
            for i, (week_start, week_end) in enumerate(weeks, 1):
                logging.info(f"Обработка недели {i}/{total_weeks}: {week_start.strftime('%Y-%m-%d')} - {week_end.strftime('%Y-%m-%d')}")
                await process_dates_range(week_start, week_end, force=args.force)
                if i < total_weeks:
                    await asyncio.sleep(2)
            
            # Дополнительно обрабатываем текущую дату, если она не попала в недели
            now = datetime.now(ESPN_TIMEZONE)
            day_start_hour = int(os.getenv('DAY_START_HOUR', '4'))
            if now.hour < day_start_hour:
                now = now - timedelta(days=1)
            current_date = now.replace(hour=day_start_hour, minute=0, second=0, microsecond=0)
            
            # Проверяем, не была ли эта дата уже обработана
            last_week_end = weeks[-1][1] if weeks else None
            if last_week_end and current_date > last_week_end:
                logging.info(f"Дополнительная обработка текущей даты: {current_date.strftime('%Y-%m-%d')}")
                await process_dates_range(current_date, current_date, force=args.force)
        else:
            # Обработка только последнего дня
            espn_now = datetime.now(ESPN_TIMEZONE)
            day_start_hour = int(os.getenv('DAY_START_HOUR', '4'))
            
            if espn_now.hour < day_start_hour:
                espn_now = espn_now - timedelta(days=1)
            
            last_day = espn_now.replace(hour=day_start_hour, minute=0, second=0, microsecond=0)
            logging.info(f"Обработка данных за последний день: {last_day.strftime('%Y-%m-%d')}")
            await process_dates_range(last_day, last_day, force=args.force)

    except KeyboardInterrupt:
        logging.info("Скрипт был прерван пользователем")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Произошла ошибка: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

def process_day_stats(data, date):
    """Обработка статистики за день"""
    logger.info(f"\n=== Начало обработки статистики за {date.strftime('%Y-%m-%d')} ===")
    
    try:
        logger.info("Получены данные от ESPN API:")
        logger.info(f"Размер данных: {len(str(data))} байт")
        logger.info("Анализ полученных данных...")
        
        # Обработка данных и формирование команды дня
        team_of_day = create_team_of_day(data)
        
        logger.info("\nСформирована команда дня:")
        for pos, player in team_of_day.items():
            logger.info(f"{pos}: {player['name']} ({player['points']} очков)")
            
        # Сохранение статистики
        update_player_stats(team_of_day, date)
        
        logger.info("\nСтатистика успешно обновлена")
        logger.info("=== Завершение обработки статистики ===\n")
        
        return team_of_day
        
    except Exception as e:
        logger.error(f"Ошибка при обработке статистики: {str(e)}")
        traceback.print_exc()
        return None
