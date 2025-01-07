#!/usr/bin/env python3

import os
import sys
import logging
import asyncio
import pytz
from datetime import datetime, timedelta
import argparse

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.espn_service import ESPNService
from src.services.image_service import ImageService
from src.services.telegram_service import TelegramService
from src.config import settings
from scripts.send_daily_teams import (
    load_history,
    get_best_players_by_position,
    update_history
)

async def process_date(
    date: datetime,
    espn_service: ESPNService,
    image_service: ImageService,
    telegram_service: TelegramService,
    history: dict,
    logger: logging.Logger,
    no_send: bool = False
):
    """Обработка статистики за указанную дату"""
    try:
        # Получаем статистику за день
        daily_stats = espn_service.get_daily_stats(date)
        
        if not daily_stats:
            logger.warning(f"Нет статистики для даты {date.strftime('%Y-%m-%d')}")
            return

        # Используем дату из полученной статистики
        date_str = daily_stats.get("date")
        if not date_str:
            logger.warning("В статистике отсутствует дата")
            return

        logger.info(f"Обработка статистики за {date_str}")

        # Формируем команду из лучших игроков
        team = get_best_players_by_position(daily_stats, date_str, history)
        
        if not team:
            logger.warning(f"Не удалось сформировать команду для даты {date_str}")
            return

        # Обновляем историю
        update_history(team, date_str, history)
        logger.info(f"История успешно обновлена для даты {date_str}")

        if not no_send:
            # Загружаем фотографии игроков
            player_photos = {}
            for pos, player in team.items():
                player_id = str(player['info']['id'])
                photo_path = image_service.get_player_photo(player_id, player['info']['name'])
                if photo_path:
                    player_photos[player_id] = photo_path
                    logger.info(f"Фото для игрока {player['info']['name']} успешно загружено")

            # Создаем коллаж
            collage_path = image_service.create_collage(player_photos, team, date_str, None)
            if not collage_path:
                logger.error("Не удалось создать коллаж")
                return

            logger.info(f"Коллаж успешно создан: {collage_path}")

            # Формируем сообщение в нужном порядке: LW, C, RW, D1, D2, G
            message = f"🏒 Команда дня - {date_str}\n\n"
            positions_order = ['LW', 'C', 'RW', 'D1', 'D2', 'G']
            for pos in positions_order:
                player = team[pos]
                message += f"{pos}: {player['info']['name']} - {player['stats']['total_points']} очков\n"

            # Отправляем в Telegram
            await telegram_service.send_team_of_day(message, collage_path)
            logger.info(f"Статистика успешно отправлена в Telegram для даты {date_str}")

    except Exception as e:
        logger.error(f"Ошибка при обработке даты {date}: {e}")
        return

async def process_week(
    start_date: datetime,
    end_date: datetime,
    espn_service: ESPNService,
    image_service: ImageService,
    telegram_service: TelegramService,
    history: dict,
    logger: logging.Logger,
    no_send: bool = False
):
    """Обработка статистики за неделю"""
    try:
        logger.info(f"Обработка периода с {start_date.strftime('%Y-%m-%d')} по {end_date.strftime('%Y-%m-%d')}")
        
        # Собираем статистику за все дни периода
        weekly_stats = {
            "date": f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}",
            "players": []
        }
        
        current_date = start_date
        while current_date <= end_date:
            daily_stats = espn_service.get_daily_stats(current_date)
            if daily_stats and "players" in daily_stats:
                weekly_stats["players"].extend(daily_stats["players"])
            current_date += timedelta(days=1)
        
        if not weekly_stats["players"]:
            logger.warning("Нет статистики за указанный период")
            return
            
        # Формируем команду периода
        team = get_best_players_by_position(weekly_stats, weekly_stats["date"], history)
        
        if not team:
            logger.warning("Не удалось сформировать команду периода")
            return
            
        if not no_send:
            # Загружаем фотографии игроков
            player_photos = {}
            for pos, player in team.items():
                player_id = str(player['info']['id'])
                photo_path = image_service.get_player_photo(player_id, player['info']['name'])
                if photo_path:
                    player_photos[player_id] = photo_path
                    logger.info(f"Фото для игрока {player['info']['name']} успешно загружено")
                    
            # Создаем коллаж команды периода
            collage_path = image_service.create_collage(player_photos, team, weekly_stats["date"], None)
            if not collage_path:
                logger.error("Не удалось создать коллаж команды периода")
                return
                
            # Формируем сообщение
            message = f"🏒 Команда периода {weekly_stats['date']}\n\n"
            positions_order = ['LW', 'C', 'RW', 'D1', 'D2', 'G']
            for pos in positions_order:
                player = team[pos]
                message += f"{pos}: {player['info']['name']} - {player['stats']['total_points']} очков\n"
                
            # Отправляем в Telegram
            await telegram_service.send_team_of_day(message, collage_path)
            logger.info("Команда периода успешно отправлена в Telegram")
            
    except Exception as e:
        logger.error(f"Ошибка при обработке периода: {e}")
        return

async def main():
    """Основная функция"""
    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Добавляем парсер аргументов
    parser = argparse.ArgumentParser(description='Перезапись статистики')
    parser.add_argument('--date', help='Конкретная дата для обработки в формате YYYY-MM-DD')
    parser.add_argument('--week', help='Период для формирования команды периода в формате YYYY-MM-DD:YYYY-MM-DD')
    parser.add_argument('--all-weeks', action='store_true', help='Обработать все периода с начала сезона')
    parser.add_argument('--no-send', action='store_true', help='Не отправлять результаты в Telegram')
    args = parser.parse_args()
    
    # Инициализируем сервисы
    espn_service = ESPNService()
    image_service = ImageService()
    telegram_service = TelegramService()
    
    # Загружаем историю
    history = load_history()
    
    if args.date:
        # Обработка одной конкретной даты
        try:
            date = datetime.strptime(args.date, '%Y-%m-%d').replace(tzinfo=pytz.UTC)
            logger.info(f"Обработка конкретной даты: {date.strftime('%Y-%m-%d')}")
            await process_date(date, espn_service, image_service, telegram_service, history, logger, args.no_send)
        except ValueError as e:
            logger.error(f"Неверный формат даты: {e}")
            return
            
    elif args.week:
        # Обработка конкретного периода
        try:
            if ':' not in args.week:
                logger.error("Неверный формат периода. Используйте YYYY-MM-DD:YYYY-MM-DD")
                return
            start_date_str, end_date_str = args.week.split(':')
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').replace(tzinfo=pytz.UTC)
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(tzinfo=pytz.UTC)
            
            if start_date > end_date:
                logger.error("Дата начала периода не может быть позже даты окончания")
                return
                
            await process_week(start_date, end_date, espn_service, image_service, telegram_service, history, logger, args.no_send)
        except ValueError as e:
            logger.error(f"Неверный формат периода: {e}")
            return
            
    elif args.all_weeks:
        # Обработка всех недель с начала сезона
        start_date = datetime(2024, 10, 4, tzinfo=pytz.UTC)  # Начало сезона
        end_date = datetime.now(pytz.UTC) - timedelta(days=1)  # Вчерашний день
        
        current_date = start_date
        while current_date <= end_date:
            # Находим начало и конец недели (понедельник-воскресенье)
            week_start = current_date - timedelta(days=current_date.weekday())  # Получаем понедельник
            week_end = week_start + timedelta(days=6)  # Получаем воскресенье
            
            if week_end > end_date:
                week_end = end_date
                
            await process_week(week_start, week_end, espn_service, image_service, telegram_service, history, logger, args.no_send)
            current_date = week_end + timedelta(days=1)  # Переходим к следующей неделе
            await asyncio.sleep(5)  # Задержка между неделями
            
    else:
        # Стандартная обработка всех дат
        start_date = datetime(2024, 10, 4, tzinfo=pytz.UTC)  # Начало сезона
        end_date = datetime.now(pytz.UTC) - timedelta(days=1)  # Вчерашний день
        
        logger.info(f"Начинаем обработку дат с {start_date.strftime('%Y-%m-%d')} по {end_date.strftime('%Y-%m-%d')}")
        
        # Обрабатываем каждую дату
        current_date = start_date
        while current_date <= end_date:
            logger.info(f"Обработка даты: {current_date.strftime('%Y-%m-%d')}")
            await process_date(current_date, espn_service, image_service, telegram_service, history, logger, args.no_send)
            current_date += timedelta(days=1)
            await asyncio.sleep(5)  # Добавляем задержку между датами

if __name__ == "__main__":
    asyncio.run(main()) 