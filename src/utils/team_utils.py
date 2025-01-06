from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

def get_best_players_by_position(players: List[Dict]) -> Optional[Dict]:
    """
    Выбирает лучших игроков по позициям
    
    Args:
        players: Список игроков с их статистикой
        
    Returns:
        Словарь с лучшими игроками по позициям или None в случае ошибки
    """
    try:
        # Группируем игроков по позициям
        players_by_position = {
            1: [], # C
            2: [], # LW
            3: [], # RW
            4: [], # D
            5: []  # G
        }
        
        for player in players:
            position = player["info"]["primary_position"]
            if position in players_by_position:
                players_by_position[position].append(player)
        
        # Сортируем игроков по очкам в каждой позиции
        for pos in players_by_position:
            players_by_position[pos].sort(
                key=lambda x: x["stats"]["total_points"],
                reverse=True
            )
        
        # Выбираем лучших игроков
        best_team = {
            "C": players_by_position[1][0] if players_by_position[1] else None,
            "LW": players_by_position[2][0] if players_by_position[2] else None,
            "RW": players_by_position[3][0] if players_by_position[3] else None,
            "D1": players_by_position[4][0] if players_by_position[4] else None,
            "D2": players_by_position[4][1] if len(players_by_position[4]) > 1 else None,
            "G": players_by_position[5][0] if players_by_position[5] else None
        }
        
        # Проверяем, что все позиции заполнены
        if None in best_team.values():
            return None
            
        return best_team
        
    except Exception as e:
        logger.error(f"Ошибка при выборе лучших игроков: {str(e)}")
        return None 