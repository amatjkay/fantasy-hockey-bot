#!/usr/bin/env python3

import json
import os
from datetime import datetime
from typing import Dict, Optional
import logging
from pathlib import Path

from src.config import settings

logger = logging.getLogger(__name__)

def load_history() -> Dict:
    """Загрузка истории команд"""
    history_file = settings.PROCESSED_DATA_DIR / "teams_history.json"
    
    if not history_file.exists():
        return {"teams": {}, "players": {}}
        
    try:
        with open(history_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке истории: {str(e)}")
        return {"teams": {}, "players": {}}

def save_history(history: Dict) -> None:
    """Сохранение истории команд"""
    history_file = settings.PROCESSED_DATA_DIR / "teams_history.json"
    
    try:
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        logger.info("История успешно сохранена")
    except Exception as e:
        logger.error(f"Ошибка при сохранении истории: {str(e)}")

def get_best_players_by_position(daily_stats: Dict, date_str: str, history: Dict) -> Optional[Dict]:
    """Получение лучших игроков по позициям"""
    try:
        players = daily_stats.get("players", [])
        if not players:
            return None
            
        # Группируем игроков по позициям
        players_by_position = {
            "C": [],
            "LW": [],
            "RW": [],
            "D": [],
            "G": []
        }
        
        for player_data in players:
            # Получаем базовую информацию об игроке
            player = player_data.get("player", {})
            if not player:
                continue
                
            position_id = player.get("defaultPositionId")
            if position_id not in settings.PLAYER_POSITIONS:
                continue
                
            position = settings.PLAYER_POSITIONS[position_id]
            
            # Получаем статистику
            if "stats" in player:
                for stat_set in player.get("stats", []):
                    if "appliedTotal" in stat_set:
                        total_points = float(stat_set.get("appliedTotal", 0))
                        if total_points > 0:
                            processed_player = {
                                "info": {
                                    "id": str(player.get("id")),
                                    "name": player.get("fullName"),
                                    "primary_position": position_id,
                                    "team_id": str(player.get("proTeamId"))
                                },
                                "stats": {
                                    "total_points": total_points
                                }
                            }
                            players_by_position[position].append(processed_player)
                            break
        
        # Сортируем игроков по очкам
        for pos in players_by_position:
            players_by_position[pos].sort(
                key=lambda x: x["stats"]["total_points"],
                reverse=True
            )
        
        # Формируем команду
        team = {}
        for pos, count in settings.TEAM_OF_DAY_COMPOSITION.items():
            if pos == "D":
                # Для защитников нам нужно два игрока
                if len(players_by_position[pos]) >= 2:
                    team["D1"] = players_by_position[pos][0]
                    team["D2"] = players_by_position[pos][1]
            else:
                if players_by_position[pos]:
                    team[pos] = players_by_position[pos][0]
        
        # Проверяем, что все позиции заполнены
        required_positions = ["C", "LW", "RW", "D1", "D2", "G"]
        if not all(pos in team for pos in required_positions):
            return None
            
        return team
        
    except Exception as e:
        logger.error(f"Ошибка при выборе лучших игроков: {str(e)}")
        return None

def update_history(team: Dict, date_str: str, history: Dict) -> None:
    """Обновление истории команд"""
    try:
        # Добавляем команду в историю
        if "teams" not in history:
            history["teams"] = {}
        history["teams"][date_str] = team
        
        # Обновляем статистику игроков
        if "players" not in history:
            history["players"] = {}
            
        for pos, player in team.items():
            player_id = str(player.get("id"))
            if player_id not in history["players"]:
                history["players"][player_id] = {
                    "name": player.get("fullName"),
                    "positions": [pos],
                    "appearances": [date_str],
                    "total_points": float(player.get("appliedStatTotal", 0))
                }
            else:
                player_stats = history["players"][player_id]
                if pos not in player_stats["positions"]:
                    player_stats["positions"].append(pos)
                player_stats["appearances"].append(date_str)
                player_stats["total_points"] += float(player.get("appliedStatTotal", 0))
                
        logger.info(f"История успешно обновлена для даты {date_str}")
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении истории: {str(e)}") 