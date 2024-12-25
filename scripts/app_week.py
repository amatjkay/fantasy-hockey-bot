import asyncio
import logging
import os
import json
from pathlib import Path
import sys

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.utils.logger import setup_logging
from src.utils.helpers import get_previous_week_dates, get_week_key
from src.services.image_service import ImageService
from src.telegram.bot import TelegramService
from src.config.settings import (
    PLAYER_STATS_FILE,
    POSITION_MAP,
    TEMP_DIR,
    ESPN_API,
    load_env_vars
)
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

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

async def main():
    """Основная функция скрипта"""
    try:
        # Проверяем переменные окружения
        env_vars = load_env_vars()
        
        # Инициализация сервисов
        image_service = ImageService()
        telegram_service = TelegramService()
        
        # Получаем даты предыдущей недели
        previous_tuesday, previous_monday = get_previous_week_dates()
        week_key = get_week_key(previous_tuesday, previous_monday)
        
        logging.info(f"Обработка команды недели: {week_key}")
        
        # Получаем команду недели
        team = get_week_team(week_key)
        if not team:
            logging.error("Не удалось получить команду недели")
            return
            
        # Проверяем, есть ли игроки в команде
        if not any(team.values()):
            logging.error("В команде недели нет игроков")
            return
            
        # Создаем временный файл для коллажа
        temp_file = TEMP_DIR / f"team_week_collage_{week_key}.jpg"
        
        try:
            # Создаем и отправляем коллаж
            photo_path = image_service.create_week_collage(team, week_key, temp_file)
            await telegram_service.send_week_results(team, week_key, photo_path)
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
    except Exception as e:
        logging.error(f"Ошибка при выполнении скрипта: {str(e)}")
        raise  # Пробрасываем исключение для отладки

if __name__ == "__main__":
    # Настраиваем логирование
    setup_logging()
    
    # Запускаем основную функцию
    asyncio.run(main()) 