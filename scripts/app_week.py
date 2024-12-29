import asyncio
import logging
import os
import json
from pathlib import Path
import sys
from datetime import datetime, timedelta
import argparse

# Добавляем корневую директорию проекта в PYTHONPATH
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from src.config.settings import ESPN_TIMEZONE
from src.utils.logger import setup_logging
from src.utils.helpers import get_previous_week_dates, get_week_key
from src.services.image_service import ImageService
from src.telegram.bot import TelegramService
from src.config.settings import (
    PLAYER_STATS_FILE,
    POSITION_MAP,
    TEMP_DIR,
    ESPN_API,
    load_env_vars,
    SEASON_START_DATE
)
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def get_all_weeks():
    """Получение списка всех недель с начала сезона"""
    weeks = []
    current_date = SEASON_START_DATE
    
    # Находим первый понедельник после начала сезона
    days_until_monday = (0 - current_date.weekday()) % 7
    first_monday = current_date + timedelta(days=days_until_monday)
    first_monday = first_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Получаем текущий понедельник
    now = datetime.now(ESPN_TIMEZONE)
    days_since_monday = now.weekday()
    current_monday = now - timedelta(days=days_since_monday)
    current_monday = current_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Генерируем все недели
    week_start = first_monday
    while week_start <= current_monday:
        week_end = week_start + timedelta(days=6)
        week_end = week_end.replace(hour=23, minute=59, second=59, microsecond=999999)
        weeks.append((week_start, week_end))
        week_start = week_start + timedelta(days=7)
    
    return weeks

def get_current_week_dates():
    """Получение дат текущей недели"""
    espn_now = datetime.now(ESPN_TIMEZONE)
    day_start_hour = int(os.getenv('DAY_START_HOUR', '4'))
    
    # Корректируем дату, если время меньше 4 утра
    if espn_now.hour < day_start_hour:
        espn_now = espn_now - timedelta(days=1)
    
    # Находим понедельник текущей недели
    days_since_monday = espn_now.weekday()
    monday = espn_now - timedelta(days=days_since_monday)
    monday = monday.replace(hour=day_start_hour, minute=0, second=0, microsecond=0)
    
    # Находим воскресенье
    sunday = monday + timedelta(days=6)
    sunday = sunday.replace(hour=day_start_hour-1, minute=59, second=59, microsecond=999999)
    
    return monday, sunday

def get_previous_week_dates():
    """Получение дат предыдущей недели"""
    espn_now = datetime.now(ESPN_TIMEZONE)
    day_start_hour = int(os.getenv('DAY_START_HOUR', '4'))
    
    # Корректируем дату, если время меньше 4 утра
    if espn_now.hour < day_start_hour:
        espn_now = espn_now - timedelta(days=1)
    
    # Находим понедельник текущей недели
    days_since_monday = espn_now.weekday()
    current_monday = espn_now - timedelta(days=days_since_monday)
    current_monday = current_monday.replace(hour=day_start_hour, minute=0, second=0, microsecond=0)
    
    # Получаем понедельник и воскресенье предыдущей недели
    previous_monday = current_monday - timedelta(days=7)
    previous_sunday = previous_monday + timedelta(days=6)
    previous_sunday = previous_sunday.replace(hour=day_start_hour-1, minute=59, second=59, microsecond=999999)
    
    return previous_monday, previous_sunday

def get_week_team(week_key):
    """Получение лучшей команды за неделю
    
    Args:
        week_key (str): Ключ недели в формате 'YYYY-MM-DD_YYYY-MM-DD'
        
    Returns:
        dict: Словарь с лучшими игроками по позициям или None в случае ошибки
    """
    try:
        with open(PLAYER_STATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        week_data = data.get("weeks", {}).get(week_key, {}).get("players", {})
        if not week_data:
            logging.error(f"Нет данных для недели {week_key}")
            return None
            
        positions = {pos: [] for pos in POSITION_MAP.keys()}
        
        for player_id, player_info in week_data.items():
            total_points = player_info.get("total_points", 0)
            name = player_info.get("name", "Unknown")
            grade = player_info.get("grade", "common")
            
            for position in player_info.get("positions", []):
                if position in positions:
                    positions[position].append({
                        'id': player_id,
                        'name': name,
                        'total_points': total_points,
                        'grade': grade,
                        'image_url': f"https://a.espncdn.com/combiner/i?img=/i/headshots/nhl/players/full/{player_id}.png&w=130&h=100"
                    })
        
        # Сортируем игроков по очкам и выбираем лучших для каждой позиции
        team = {}
        empty_positions = []
        for position, count in POSITION_MAP.items():
            if positions[position]:
                sorted_players = sorted(positions[position], key=lambda x: x['total_points'], reverse=True)
                team[position] = sorted_players[:count]
            else:
                empty_positions.append(position)
                team[position] = []
        
        if empty_positions:
            logging.warning(f"Нет игроков на позициях: {', '.join(empty_positions)}")
            
        return team
    except FileNotFoundError:
        logging.error(f"Файл статистики не найден: {PLAYER_STATS_FILE}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Ошибка чтения JSON из файла: {PLAYER_STATS_FILE}")
        return None
    except Exception as e:
        logging.error(f"Ошибка при получении команды недели: {str(e)}")
        return None

async def process_week(week_start, week_end, image_service, telegram_service):
    """Обработка одной недели"""
    week_key = get_week_key(week_start, week_end)
    logging.info(f"Обработка команды недели: {week_key}")
    
    # Получаем команду недели
    team = get_week_team(week_key)
    if not team:
        logging.error(f"Не удалось получить команду недели для {week_key}")
        return
        
    # Проверяем, есть ли игроки в команде
    if not any(team.values()):
        logging.error(f"В команде недели нет игроков для {week_key}")
        return
        
    # Создаем временный файл для коллажа
    temp_file = TEMP_DIR / f"team_week_collage_{week_key}.jpg"
    
    try:
        # Создаем и отправляем коллаж
        photo_path = image_service.create_week_collage(team, week_key, temp_file)
        await telegram_service.send_week_results(team, week_key, photo_path)
        # Небольшая пауза между отправками
        await asyncio.sleep(2)
    finally:
        # Удаляем временный файл
        if os.path.exists(temp_file):
            os.remove(temp_file)

async def main():
    """Основная функция скрипта"""
    try:
        # Парсим аргументы командной строки
        parser = argparse.ArgumentParser(description='Скрипт для создания команд недели')
        parser.add_argument('--all-weeks', action='store_true', help='Обработать все недели с начала сезона')
        args = parser.parse_args()
        
        # Проверяем переменные окружения
        env_vars = load_env_vars()
        
        # Инициализация сервисов
        image_service = ImageService()
        telegram_service = TelegramService()
        
        if args.all_weeks:
            # Получаем все недели
            weeks = get_all_weeks()
            logging.info(f"Начинаем обработку всех недель ({len(weeks)} недель)")
            
            for week_start, week_end in weeks:
                await process_week(week_start, week_end, image_service, telegram_service)
        else:
            # Обрабатываем только предыдущую неделю
            previous_monday, previous_sunday = get_previous_week_dates()
            await process_week(previous_monday, previous_sunday, image_service, telegram_service)
            
    except Exception as e:
        logging.error(f"Ошибка при выполнении скрипта: {str(e)}")
        raise

if __name__ == "__main__":
    # Настраиваем логирование
    setup_logging()
    
    # Запускаем основную функцию
    asyncio.run(main()) 