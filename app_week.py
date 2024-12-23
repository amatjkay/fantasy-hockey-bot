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
import sys
import traceback
import requests

def debug_print(message):
    """Вывод отладочной информации"""
    print(f"[DEBUG] {message}")
    sys.stdout.flush()

def ensure_directory_exists(file_path):
    """Создание директории для файла, если она не существует"""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

# Конфигурация путей
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_FILE = os.path.join(BASE_DIR, "week_log.txt")
ESPN_TIMEZONE = pytz.timezone('US/Eastern')
PLAYER_STATS_FILE = os.path.join(BASE_DIR, "player_stats.json")
WEEKLY_STATS_FILE = os.path.join(BASE_DIR, "weekly_team_stats.json")
ENV_FILE = os.path.join(BASE_DIR, ".env")

POSITION_MAP = {
    'C': 1,
    'LW': 1,
    'RW': 1,
    'D': 2,
    'G': 1
}

GRADE_PRIORITY = {
    "legend": 5,
    "epic": 4,
    "rare": 3,
    "uncommon": 2,
    "common": 1
}

GRADE_COLORS = {
    "common": "black",
    "uncommon": "green",
    "rare": "blue",
    "epic": "purple",
    "legend": "orange"
}

debug_print(f"Текущая директория: {os.getcwd()}")
debug_print(f"Базовая директория: {BASE_DIR}")
debug_print(f"Файл логов: {LOG_FILE}")

try:
    # Настройка логирования
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Добавляем файловый обработчик отдельно
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8', mode='a')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)
    
    debug_print("Логирование настроено успешно")
    logging.info("Начало работы скрипта")
except Exception as e:
    debug_print(f"Ошибка при настройке логирования: {e}")
    traceback.print_exc()
    sys.exit(1)

# Загрузка переменных окружения
load_dotenv(ENV_FILE)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

if not TELEGRAM_TOKEN or not CHAT_ID:
    logging.error("TELEGRAM_TOKEN или CHAT_ID не установлены в файле .env")
    exit(1)

bot = Bot(token=TELEGRAM_TOKEN)

def get_week_dates(date):
    """Получение дат начала и конца недели для заданной даты"""
    days_since_tuesday = (date.weekday() - 1) % 7
    tuesday = date - timedelta(days=days_since_tuesday)
    tuesday = tuesday.replace(hour=0, minute=0, second=0, microsecond=0)
    monday = tuesday + timedelta(days=6)
    monday = monday.replace(hour=23, minute=59, second=59, microsecond=999999)
    return tuesday, monday

def load_player_stats():
    """Загрузка статистики игроков"""
    try:
        with open(PLAYER_STATS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка при загрузке статистики игроков: {e}")
        return {"weeks": {}}

def load_weekly_stats():
    """Загрузка статистики команд недели"""
    try:
        with open(WEEKLY_STATS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"weeks": {}}

def save_weekly_stats(stats):
    """Сохранение статистики команд недели"""
    with open(WEEKLY_STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=4)

def calculate_weekly_team(week_key, players_data):
    """Формирование команды недели на основе грейдов и очков"""
    positions = {'C': [], 'LW': [], 'RW': [], 'D': [], 'G': []}
    debug_print(f"\nОбработка недели {week_key}")
    debug_print(f"Всего игроков в неделе: {len(players_data)}")
    
    # Группировка игроков по позициям и подсчет общих очков
    for player_id, player_data in players_data.items():
        if 'team_of_the_day_dates' not in player_data:
            continue

        # Count appearances per position and calculate total points
        position_appearances = {}
        position_points = {}
        
        for date_pos in player_data['team_of_the_day_dates']:
            pos, date = date_pos.split(':')  # Split "C:2024-12-15" into position and date
            position_appearances[pos] = position_appearances.get(pos, 0) + 1
            
            # Добавляем очки для поз��ции
            if date in player_data.get('daily_stats', {}):
                points = player_data['daily_stats'][date].get('points', 0)
                position_points[pos] = position_points.get(pos, 0) + points

        grade = player_data.get('grade', 'common')
        name = player_data.get('name', 'Unknown')
        
        debug_print(f"Игрок: {name}, Позиции: {position_appearances.keys()}, Грейд: {grade}")
        debug_print(f"Даты появления: {player_data.get('team_of_the_day_dates', [])}")

        # Add player to each position they appeared in
        for position, count in position_appearances.items():
            if position in positions:
                positions[position].append({
                    'id': player_id,
                    'name': name,
                    'total_points': count,  # количество появлений
                    'weekly_points': position_points.get(position, 0),  # сумма очков за неделю
                    'grade': grade,
                    'grade_priority': GRADE_PRIORITY.get(grade, 0)
                })
                debug_print(f"Добавлен в позицию {position} с {count} появлениями и {position_points.get(position, 0)} очками")

    # Выбор лучших игроков для каждой позиции
    team = {}
    for position, count in POSITION_MAP.items():
        debug_print(f"\nПозиция {position}:")
        debug_print(f"Всего кандидатов: {len(positions[position])}")
        
        if not positions[position]:
            debug_print(f"ВНИМАНИЕ: Нет кандидатов для позиции {position}")
            team[position] = []
            continue
        
        # Сортировка по грейду (приоритет) и количеству появлений
        sorted_players = sorted(
            positions[position],
            key=lambda x: (x['grade_priority'], x['total_points'], x['weekly_points']),
            reverse=True
        )
        
        # Выбираем лучших игроков для позиции
        team[position] = sorted_players[:count]
        
        # Логируем выбранных игроков
        for player in team[position]:
            debug_print(f"Выбран: {player['name']} (Грейд: {player['grade']}, Появлений: {player['total_points']}, Очки: {player['weekly_points']})")

    return team

def create_weekly_collage(team, week_str):
    """Создание коллажа команды недели"""
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
    
    title = f"Команда недели {week_str}"
    title_width = draw.textlength(title, font=font)
    draw.text(((width - title_width) // 2, y_offset), title, fill="black", font=font)
    y_offset += 40

    for position, players in team.items():
        for player in players:
            name = player['name']
            appearances = player['total_points']
            weekly_points = player.get('weekly_points', 0)
            grade = player['grade']
            color = GRADE_COLORS.get(grade, "black")
            player_id = player['id']

            try:
                image_url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/nhl/players/full/{player_id}.png&w=130&h=100"
                response = requests.get(image_url, stream=True, timeout=10)
                response.raise_for_status()
                player_image = Image.open(response.raw).convert("RGBA")
                bg = Image.new("RGBA", player_image.size, (255, 255, 255, 255))
                combined_image = Image.alpha_composite(bg, player_image)
                player_image = combined_image.convert("RGB").resize((player_img_width, player_img_height), Image.LANCZOS)
                image_x = (width - player_img_width) // 2
                image.paste(player_image, (image_x, y_offset))
            except Exception as e:
                debug_print(f"Ошибка загрузки изображения для {name}: {e}")
                empty_img = Image.new("RGB", (player_img_width, player_img_height), "gray")
                image_x = (width - player_img_width) // 2
                image.paste(empty_img, (image_x, y_offset))

            # Формируем текст
            if appearances > 1:
                text = f"{position}: {name} [{appearances}] {weekly_points:.1f} ftps"
            else:
                text = f"{position}: {name} {weekly_points:.1f} ftps"
            
            text_width = draw.textlength(text, font=font)
            text_x = (width - text_width) // 2
            draw.text((text_x, y_offset + player_img_height + text_padding), text, fill=color, font=font)
            y_offset += line_height

    temp_file = f"weekly_team_{week_str}.jpg"
    image.save(temp_file)
    return temp_file

async def send_weekly_team(team, week_str):
    """Отправка команды недели в Telegram"""
    try:
        temp_file = create_weekly_collage(team, week_str)
        
        with open(temp_file, 'rb') as photo:
            await bot.send_photo(
                chat_id=CHAT_ID,
                photo=photo,
                parse_mode=ParseMode.HTML
            )
        
        if os.path.exists(temp_file):
            os.remove(temp_file)

    except Exception as e:
        logging.error(f"Ошибка при отправке команды недели: {e}")

async def process_all_weeks():
    """Обработка всех недель"""
    try:
        debug_print("Загрузка статистики игроков")
        player_stats = load_player_stats()
        if not player_stats or 'weeks' not in player_stats:
            debug_print("О��ибка: Не найдена статистика игроков")
            return
        debug_print(f"Загружено недель: {len(player_stats.get('weeks', {}))}")
        
        debug_print("Загрузка статистики команд недели")
        weekly_stats = load_weekly_stats()
        debug_print(f"Уже обработано недель: {len(weekly_stats.get('weeks', {}))}")
        
        weeks_to_process = []
        for week_key, week_data in player_stats['weeks'].items():
            if 'players' not in week_data:
                debug_print(f"Пропуск недели {week_key}: нет данных об игроках")
                continue
            if not week_data['players']:
                debug_print(f"Пропуск недели {week_key}: пустой список игроков")
                continue
            weeks_to_process.append(week_key)
        
        debug_print(f"Предстоит обработать недель: {len(weeks_to_process)}")
        
        for week_key in weeks_to_process:
            debug_print(f"\n{'='*50}")
            debug_print(f"Обработка недели: {week_key}")
            
            week_data = player_stats['weeks'][week_key]
            team = calculate_weekly_team(week_key, week_data['players'])
            
            if not any(team.values()):
                debug_print("Предупреждение: Не найдено игроков для команды недели")
                continue
            
            # Save the team data for this week
            weekly_stats.setdefault('weeks', {})[week_key] = team
            save_weekly_stats(weekly_stats)
            debug_print(f"Сохранена статистика для недели {week_key}")
            
            try:
                debug_print("Отправка команды недели в Telegram")
                await send_weekly_team(team, week_key)
            except Exception as e:
                debug_print(f"Ошибка при отправке команды недели: {e}")
            
            await asyncio.sleep(2)
            
        debug_print("\nОбработка всех недель завершена")
        
    except Exception as e:
        debug_print(f"Ошибка при обработке недель: {e}")
        logging.error(f"Ошибка при обработке недель: {e}")
        traceback.print_exc()

async def main():
    logging.info("Начало формирования команд недели")
    await process_all_weeks()
    logging.info("З��вершено формирование команд недели")

if __name__ == "__main__":
    asyncio.run(main()) 