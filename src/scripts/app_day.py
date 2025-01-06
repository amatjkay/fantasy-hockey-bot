import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List
from src.services.stats_service import StatsService
from src.services.image_service import ImageService
from src.services.telegram_service import TelegramService
from src.config.settings import (
    ESPN_API,
    ESPN_TIMEZONE,
    PROCESSED_DATA_DIR,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_season_stats() -> Dict:
    """Загружает статистику за сезон"""
    stats_file = os.path.join(PROCESSED_DATA_DIR, 'season_stats.json')
    if not os.path.exists(stats_file):
        raise FileNotFoundError(f"Файл статистики не найден: {stats_file}")
        
    with open(stats_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_best_players(daily_stats: Dict) -> Dict[str, List]:
    """Определяет лучших игроков дня по позициям"""
    players = daily_stats.get('players', [])
    if not players:
        logger.warning("Нет данных об игроках")
        return {}
    
    # Структура для хранения лучших игроков по позициям
    best_players = {
        'C': [],  # Центральные
        'LW': [], # Левые крайние
        'RW': [], # Правые крайние
        'D': [],  # Защитники
        'G': []   # Вратари
    }
    
    # Маппинг позиций
    position_map = {
        1: 'C',   # Center
        2: 'LW',  # Left Wing
        3: 'RW',  # Right Wing
        4: 'D',   # Defense
        5: 'G'    # Goalie
    }
    
    # Сортируем игроков по очкам и распределяем по позициям
    for player_data in players:
        player = player_data.get('player', {})
        if not player:
            continue
            
        position_id = player.get('defaultPositionId')
        if not position_id or position_id not in position_map:
            continue
            
        position = position_map[position_id]
        stats = player_data.get('stats', {})
        
        if not stats:
            continue
            
        # Подсчет очков в зависимости от позиции
        points = 0
        if position == 'G':
            # Для вратарей
            points = (
                stats.get('wins', 0) * 5 +
                stats.get('saves', 0) * 0.2 +
                stats.get('shutouts', 0) * 3 -
                stats.get('goalsAgainst', 0) * 1
            )
        else:
            # Для полевых игроков
            points = (
                stats.get('goals', 0) * 3 +
                stats.get('assists', 0) * 2 +
                stats.get('plusMinus', 0) * 1 +
                stats.get('powerPlayPoints', 0) * 1 +
                stats.get('shots', 0) * 0.2 +
                stats.get('hits', 0) * 0.2 +
                stats.get('blockedShots', 0) * 0.5
            )
        
        best_players[position].append({
            'id': player.get('id'),
            'name': player.get('fullName'),
            'team': player.get('proTeamId'),
            'points': round(points, 1),
            'stats': stats
        })
    
    # Сортируем игроков по очкам и берем топ-N для каждой позиции
    for pos in best_players:
        best_players[pos] = sorted(
            best_players[pos],
            key=lambda x: x['points'],
            reverse=True
        )[:3 if pos != 'G' else 2]  # 3 игрока для всех позиций кроме вратарей
    
    return best_players

def create_team_message(date: str, best_players: Dict[str, List]) -> str:
    """Создает сообщение с составом команды дня"""
    if not best_players:
        return f"🏒 За {date} нет данных об игроках"
    
    message = f"🏒 Команда дня {date}\n\n"
    
    positions = {
        'C': '⚡️ Центральные:',
        'LW': '🏃 Левые крайние:',
        'RW': '💨 Правые крайние:',
        'D': '🛡 Защитники:',
        'G': '🥅 Вратари:'
    }
    
    for pos, title in positions.items():
        if pos in best_players and best_players[pos]:
            message += f"\n{title}\n"
            for player in best_players[pos]:
                message += f"- {player['name']} ({player['points']} очков)\n"
    
    return message

def main():
    """Основная функция"""
    try:
        # Загружаем статистику
        season_stats = load_season_stats()
        
        # Инициализируем сервисы
        image_service = ImageService()
        telegram_service = TelegramService(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        
        # Обрабатываем каждый день
        for daily_stat in season_stats['daily_stats']:
            date = daily_stat['date']
            logger.info(f"Обработка данных за {date}")
            
            try:
                # Определяем лучших игроков
                best_players = get_best_players(daily_stat)
                
                # Формируем сообщение
                message = create_team_message(date, best_players)
                
                if best_players:
                    # Создаем коллаж
                    collage_path = image_service.create_team_collage(best_players, date)
                    
                    # Отправляем в Telegram
                    telegram_service.send_photo(collage_path, message)
                    
                    # Удаляем временный файл коллажа
                    if os.path.exists(collage_path):
                        os.remove(collage_path)
                else:
                    # Отправляем только сообщение
                    telegram_service.send_message(message)
                
                logger.info(f"Данные за {date} успешно обработаны и отправлены")
                
                # Добавляем задержку между запросами
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Ошибка при обработке данных за {date}: {str(e)}")
                continue
            
    except Exception as e:
        logger.error(f"Ошибка при обработке данных: {str(e)}")
        raise

if __name__ == '__main__':
    main() 