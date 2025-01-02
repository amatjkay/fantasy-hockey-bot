#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import argparse
import json
from datetime import datetime, timedelta
import traceback
from dotenv import load_dotenv

from src.services.espn_service import ESPNService
from src.services.image_service import ImageService
from src.services.telegram_service import TelegramService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description='Получение команды дня')
    parser.add_argument('--date', help='Дата в формате YYYY-MM-DD')
    parser.add_argument('--force', action='store_true', help='Принудительное обновление')
    return parser.parse_args()

def get_week_key(date):
    """Получение ключа недели для даты"""
    # Получаем понедельник текущей недели
    monday = date - timedelta(days=date.weekday())
    # Получаем воскресенье текущей недели
    sunday = monday + timedelta(days=6)
    return f"{monday.strftime('%Y-%m-%d')}_{sunday.strftime('%Y-%m-%d')}"

def update_player_stats(team, date):
    """Обновление статистики игроков
    
    Args:
        team (list): Список игроков команды дня
        date (datetime): Дата команды дня
    """
    try:
        stats_file = 'data/processed/player_stats.json'
        
        # Загружаем текущую статистику
        if os.path.exists(stats_file):
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
        else:
            stats = {"weeks": {}}
        
        # Получаем ключ недели
        week_key = get_week_key(date)
        date_str = date.strftime('%Y-%m-%d')
        
        # Инициализируем данные недели если их нет
        if week_key not in stats["weeks"]:
            stats["weeks"][week_key] = {"players": {}}
        
        # Обновляем статистику каждого игрока
        for player in team:
            player_id = str(player['id'])
            
            # Инициализируем данные игрока если их нет
            if player_id not in stats["weeks"][week_key]["players"]:
                stats["weeks"][week_key]["players"][player_id] = {
                    "name": player['name'],
                    "positions": [player['position']],
                    "team_of_the_day_count": 0,
                    "grade": "common",
                    "daily_stats": {},
                    "dates_in_team": []  # Список дат попадания в команду дня
                }
            
            player_stats = stats["weeks"][week_key]["players"][player_id]
            
            # Проверяем, не обрабатывали ли мы уже эту дату для данного игрока
            if date_str not in player_stats.get("dates_in_team", []):
                # Добавляем дату в список
                if "dates_in_team" not in player_stats:
                    player_stats["dates_in_team"] = []
                player_stats["dates_in_team"].append(date_str)
                
                # Увеличиваем счетчик попаданий в команду дня
                player_stats["team_of_the_day_count"] = len(player_stats["dates_in_team"])
                
                # Обновляем грейд на основе количества уникальных дат
                count = player_stats["team_of_the_day_count"]
                if count >= 5:
                    player_stats["grade"] = "legend"
                elif count == 4:
                    player_stats["grade"] = "epic"
                elif count == 3:
                    player_stats["grade"] = "rare"
                elif count == 2:
                    player_stats["grade"] = "uncommon"
                else:
                    player_stats["grade"] = "common"
                
                # Обновляем грейд в объекте игрока для текущей команды
                player['grade'] = player_stats["grade"]
            else:
                # Если дата уже обработана, используем существующий грейд
                player['grade'] = player_stats["grade"]
            
            # Обновляем или добавляем статистику за день
            player_stats["daily_stats"][date_str] = {
                "points": player['stats'][0]['points'],
                "total_points": player['stats'][0]['totalPoints']
            }
            
            # Для вратарей добавляем процент отраженных бросков
            if player['position'] == 'G' and 'savePct' in player['stats'][0]:
                player_stats["daily_stats"][date_str]["savePct"] = player['stats'][0]['savePct']
        
        # Сохраняем обновленную статистику
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Статистика успешно обновлена для даты {date_str}")
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении статистики: {e}")
        traceback.print_exc()

def main():
    """Основная функция скрипта"""
    try:
        # Загружаем переменные окружения
        load_dotenv()
        
        # Получаем дату из аргументов командной строки
        args = parse_args()
        if args.date:
            date = datetime.strptime(args.date, '%Y-%m-%d')
        else:
            date = datetime.now()
        
        # Инициализируем сервисы
        espn_service = ESPNService()
        image_service = ImageService()
        telegram_service = TelegramService()
        
        # Получаем статистику
        team = espn_service.get_team_of_the_day(date)
        
        if not team:
            logger.error("Не удалось получить статистику")
            return
            
        # Обновляем статистику игроков
        update_player_stats(team, date)
        
        # Обновляем грейды в ESPNService
        espn_service.update_player_grades()
            
        # Создаем коллаж
        output_path = 'data/output/team_collage.png'
        if image_service.create_team_collage(team, output_path, date):
            logger.info(f"Коллаж сохранен: {output_path}")
            
            # Отправляем в Telegram
            telegram_service.send_team_of_the_day()
        else:
            logger.error("Не удалось создать коллаж")
            
    except Exception as e:
        logger.error(f"Ошибка при выполнении скрипта: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
