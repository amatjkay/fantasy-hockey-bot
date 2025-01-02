import logging
from datetime import datetime
from typing import Dict, List, Optional
from .espn_service import ESPNService

class StatsService:
    def __init__(self):
        self.espn_service = ESPNService()
        self.logger = logging.getLogger(__name__)
        self.positions = {
            'C': 2,   # Центральные нападающие
            'LW': 2,  # Левые нападающие
            'RW': 2,  # Правые нападающие
            'D': 4,   # Защитники
            'G': 2    # Вратари
        }

    def get_team_of_the_day(self, date: Optional[datetime] = None) -> Dict[str, List[dict]]:
        """Получение команды дня
        
        Args:
            date (datetime, optional): Дата для получения статистики
            
        Returns:
            Dict[str, List[dict]]: Словарь с игроками по позициям
        """
        try:
            stats = self.espn_service.get_daily_stats(date)
            if not stats or 'players' not in stats:
                self.logger.error("Не удалось получить статистику")
                return {}

            # Группируем игроков по позициям
            players_by_position = self._group_players_by_position(stats['players'])
            
            # Выбираем лучших игроков для каждой позиции
            team = {}
            for position, count in self.positions.items():
                if position in players_by_position:
                    team[position] = self._get_best_players(
                        players_by_position[position], 
                        count
                    )
                else:
                    team[position] = []

            return team
        except Exception as e:
            self.logger.error(f"Ошибка при формировании команды дня: {e}")
            return {}

    def _group_players_by_position(self, players: List[dict]) -> Dict[str, List[dict]]:
        """Группировка игроков по позициям"""
        result = {}
        for player in players:
            if 'defaultPositionId' not in player:
                continue
                
            position = self._get_position_code(player['defaultPositionId'])
            if position:
                if position not in result:
                    result[position] = []
                result[position].append({
                    'id': str(player['id']),
                    'name': player['fullName'],
                    'stats': player.get('stats', [{}])[0],
                    'position': position
                })
        return result

    def _get_best_players(self, players: List[dict], count: int) -> List[dict]:
        """Выбор лучших игроков на позиции"""
        # Сортируем по очкам (для полевых игроков) или проценту отраженных бросков (для вратарей)
        if players and players[0]['position'] == 'G':
            sorted_players = sorted(
                players, 
                key=lambda x: x['stats'].get('savePct', 0) if x['stats'] else 0,
                reverse=True
            )
        else:
            sorted_players = sorted(
                players,
                key=lambda x: x['stats'].get('totalPoints', 0) if x['stats'] else 0,
                reverse=True
            )
        
        return sorted_players[:count]

    def _get_position_code(self, position_id: int) -> Optional[str]:
        """Преобразование ID позиции в код"""
        position_map = {
            1: 'C',
            2: 'LW',
            3: 'RW',
            4: 'D',
            5: 'G'
        }
        return position_map.get(position_id)
