from typing import Dict, List, Optional
from datetime import datetime
import logging
from .stats_service import StatsService
from .image_service import ImageService
from ..config import settings
from collections import defaultdict

logger = logging.getLogger(__name__)

class TeamWeekService:
    def __init__(self):
        self.stats_service = StatsService()
        self.image_service = ImageService()
        
    def get_team_of_week(self, start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """Формирует команду недели"""
        weekly_stats = self.stats_service.get_team_of_the_week(start_date, end_date)
        if not weekly_stats:
            logger.error(f"Не удалось получить статистику за период {start_date} - {end_date}")
            return None
            
        # Группируем игроков по позициям
        players_by_position = self._group_players_by_position(weekly_stats["players"])
        
        # Формируем команду согласно требуемому составу
        team = {
            "date": weekly_stats["date"],
            "players": self._select_best_players(players_by_position),
            "total_points": 0
        }
        
        # Считаем общие очки команды
        team["total_points"] = sum(
            player["stats"]["total_points"] 
            for player in team["players"].values()
        )
        
        return team
        
    def _group_players_by_position(self, players: List[Dict]) -> Dict[str, List[Dict]]:
        """Группирует игроков по позициям"""
        grouped_players = defaultdict(list)
        
        for player in players:
            position_id = player["info"]["primary_position"]
            if position_id in settings.PLAYER_POSITIONS:
                position = settings.PLAYER_POSITIONS[position_id]
                # Добавляем только игроков с положительными очками
                if player["stats"]["total_points"] > 0:
                    grouped_players[position].append(player)
        
        # Сортируем игроков по очкам в каждой позиции
        for position in grouped_players:
            grouped_players[position].sort(
                key=lambda x: x["stats"]["total_points"],
                reverse=True
            )
        
        return dict(grouped_players)
        
    def _select_best_players(self, players_by_position: Dict) -> Dict:
        """Выбирает лучших игроков для команды недели"""
        selected = {}
        
        # Выбираем нужное количество игроков для каждой позиции
        for position, count in settings.TEAM_OF_DAY_COMPOSITION.items():
            players = players_by_position.get(position, [])
            # Выбираем лучших игроков для каждой позиции
            for i, player in enumerate(players[:count]):
                pos_key = position if count == 1 else f"{position}{i+1}"
                selected[pos_key] = player
                logger.info(f"Выбран игрок {player['info']['name']} ({pos_key}) с {player['stats']['total_points']} очками")
        
        return selected
        
    def create_team_collage(self, team: Dict) -> Optional[str]:
        """Создает коллаж команды"""
        # Получаем фото всех игроков
        player_photos = {}
        for pos, player_data in team["players"].items():
            # Добавляем поле position на основе primary_position
            player_data["info"]["position"] = settings.PLAYER_POSITIONS[player_data["info"]["primary_position"]]
            photo = self.image_service.get_player_photo(
                str(player_data["info"]["id"]),
                player_data["info"]["name"]
            )
            if photo:
                player_photos[str(player_data["info"]["id"])] = photo
                
        if len(player_photos) != len(team["players"]):
            logger.warning("Не удалось получить фото всех игроков")
            
        # Создаем коллаж
        return self.image_service.create_team_collage(
            player_photos,
            team["players"],
            team["date"]
        ) 