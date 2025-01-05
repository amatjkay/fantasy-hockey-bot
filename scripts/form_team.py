#!/usr/bin/env python3
import os
import sys
import json
import logging
import random
from typing import Dict, List, Optional, Set
from datetime import datetime
from src.config.settings import PROCESSED_DATA_DIR

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_stats() -> Optional[Dict]:
    """Загружает статистику из файла"""
    try:
        stats_file = os.path.join(PROCESSED_DATA_DIR, 'season_stats.json')
        with open(stats_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading stats: {e}")
        return None

def calculate_player_score(player: Dict) -> float:
    """Вычисляет общий счет игрока на основе его статистики"""
    total_score = 0
    for stat in player.get('stats', []):
        total_score += stat.get('appliedTotal', 0)
    return total_score

def get_position_name(position_id: int) -> str:
    """Возвращает название позиции по её ID"""
    positions = {
        0: "C",   # Center
        1: "LW",  # Left Wing
        2: "RW",  # Right Wing
        3: "F",   # Forward (может быть C/LW/RW)
        4: "D",   # Defense
        5: "G"    # Goalie
    }
    return positions.get(position_id, "Unknown")

def get_player_positions(player: Dict) -> List[str]:
    """Определяет все возможные позиции игрока"""
    position_id = player['defaultPositionId']
    eligible_slots = player.get('eligibleSlots', [])
    
    # Возвращаем только основную позицию игрока
    position = get_position_name(position_id)
    return [position] if position != "Unknown" else []

def select_best_players(players: List[Dict], num_players: int = 1, used_players: Set[int] = None) -> List[Dict]:
    """Выбирает лучших игроков с учетом случайного выбора при равных очках"""
    if not players:
        return []
        
    if used_players is None:
        used_players = set()
        
    # Отфильтровываем уже использованных игроков
    available_players = [p for p in players if p['id'] not in used_players]
    if not available_players:
        return []
        
    # Сортируем игроков по очкам
    sorted_players = sorted(available_players, key=lambda x: x['score'], reverse=True)
    
    # Выбираем игроков с лучшим результатом
    best_score = sorted_players[0]['score']
    best_players = [p for p in sorted_players if p['score'] == best_score]
    
    # Если есть несколько игроков с одинаковым результатом, выбираем случайно
    if len(best_players) > num_players:
        selected = random.sample(best_players, num_players)
        for player in selected:
            used_players.add(player['id'])
        return selected
    
    # Если лучших игроков меньше чем нужно, добавляем следующих по очкам
    result = best_players
    for player in result:
        used_players.add(player['id'])
        
    remaining_players = [p for p in sorted_players if p not in best_players and p['id'] not in used_players]
    
    while len(result) < num_players and remaining_players:
        next_score = remaining_players[0]['score']
        next_players = [p for p in remaining_players if p['score'] == next_score]
        
        if len(result) + len(next_players) <= num_players:
            for player in next_players:
                used_players.add(player['id'])
            result.extend(next_players)
            remaining_players = [p for p in remaining_players if p not in next_players]
        else:
            needed = num_players - len(result)
            selected = random.sample(next_players, needed)
            for player in selected:
                used_players.add(player['id'])
            result.extend(selected)
            break
            
    return result

def get_player_position(player):
    position_id = player['defaultPositionId']
    eligible_slots = player.get('eligibleSlots', [])
    
    # Если игрок может играть в центре (слот 0) и его основная позиция - нападающий
    if 0 in eligible_slots and position_id in [1, 2, 3]:
        return 'C'
    # Если игрок может играть слева (слот 1) и его основная позиция - нападающий
    elif position_id == 1 and 1 not in eligible_slots:
        return 'LW'
    elif position_id == 2:
        return 'RW'
    elif position_id == 3:
        return 'F'
    elif position_id == 4:
        return 'D'
    elif position_id == 5:
        return 'G'
    else:
        return None

def form_team(stats: Dict) -> Dict:
    """Формирует команду на основе статистики"""
    logger = logging.getLogger(__name__)
    
    # Словарь для хранения игроков по позициям
    positions = {'C': [], 'LW': [], 'RW': [], 'D': [], 'G': []}
    used_players = set()
    
    # Собираем статистику по всем игрокам за все дни
    all_players = {}  # id -> player_info
    
    for date, day_stats in stats['stats'].items():
        for player in day_stats['players']:
            player_id = player['id']
            
            # Выводим информацию о позиции игрока
            logger.info(f"Игрок: {player['fullName']}, ID позиции: {player['defaultPositionId']}, слоты: {player.get('eligibleSlots', [])}")
            
            # Если игрок уже обработан, обновляем его статистику
            if player_id in all_players:
                current_score = calculate_player_score(player)
                if current_score > all_players[player_id]['score']:
                    # Обновляем статистику, если текущий результат лучше
                    all_players[player_id].update({
                        'score': current_score,
                        'stats': player['stats']
                    })
            else:
                # Получаем позицию игрока
                position = get_player_position(player)
                
                if not position:
                    logger.warning(f"Неизвестная позиция для игрока {player['fullName']}: {player['defaultPositionId']}")
                    continue
                    
                # Вычисляем общий счет игрока
                score = calculate_player_score(player)
                
                # Создаем информацию об игроке
                player_info = {
                    'id': player_id,
                    'name': player['fullName'],
                    'position': position,
                    'score': score,
                    'stats': player['stats']
                }
                
                all_players[player_id] = player_info
    
    # Сортируем игроков по убыванию очков для каждой позиции
    for position in positions:
        position_players = [p for p in all_players.values() if p['position'] == position]
        sorted_players = sorted(position_players, key=lambda x: x['score'], reverse=True)
        
        # Выбираем лучших игроков для каждой позиции
        max_players = get_max_players_for_position(position)
        for player in sorted_players:
            if player['id'] not in used_players and len(positions[position]) < max_players:
                positions[position].append(player)
                used_players.add(player['id'])
                logger.info(f"Добавлен игрок {player['name']} на позицию {position}")
    
    return positions

def get_max_players_for_position(position):
    return {
        'C': 1,   # 1 центральный нападающий
        'LW': 1,  # 1 левый нападающий
        'RW': 1,  # 1 правый нападающий
        'D': 2,   # 2 защитника
        'G': 1    # 1 вратарь
    }[position]

def main():
    """Основная функция"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Загружаем статистику
        stats = load_stats()
        if not stats:
            logger.error("Не удалось загрузить статистику")
            sys.exit(1)
        
        # Формируем команду
        team = form_team(stats)
        
        # Выводим результаты
        logger.info("\nСформированная команда:")
        total_score = 0
        
        # Порядок вывода позиций
        position_order = ["C", "LW", "RW", "D", "G"]
        
        for position in position_order:
            players = team[position]
            if not players:
                logger.warning(f"\n{position}: Нет подходящих игроков")
                continue
                
            logger.info(f"\n{position}:")
            position_score = 0
            
            for player in players:
                logger.info(f"  {player['name']} (Score: {player['score']:.2f})")
                position_score += player['score']
                total_score += player['score']
                
            logger.info(f"  Общий счет позиции: {position_score:.2f}")
            
        logger.info(f"\nОбщий счет команды: {total_score:.2f}")
        
    except Exception as e:
        logger.error(f"Ошибка выполнения скрипта: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main() 