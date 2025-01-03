import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from src.services.espn_service import ESPNService
from src.utils.logging import setup_logging
from src.config import (
    DATA_DIR,
    PROCESSED_DIR,
    TEAMS_HISTORY_FILE,
    PLAYER_GRADES_FILE,
    POSITION_MAPPING,
    GRADE_MAPPING
)

class StatsService:
    """Сервис для работы со статистикой игроков и команд"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.logger = setup_logging('stats')
        self.espn_service = ESPNService()
        
        # Количество игроков на каждой позиции
        self.positions = {
            'C': 1,   # Центральный нападающий
            'LW': 1,  # Левый нападающий
            'RW': 1,  # Правый нападающий
            'D': 2,   # Защитники
            'G': 1    # Вратарь
        }
        
        # Пути к файлам данных
        self.player_stats_file = os.path.join(PROCESSED_DIR, 'player_stats.json')
        self.season_stats_file = os.path.join(PROCESSED_DIR, 'season_stats.json')
        self.teams_history_file = TEAMS_HISTORY_FILE
        self.weekly_stats_file = os.path.join(PROCESSED_DIR, 'weekly_team_stats.json')
        
        # Загружаем существующие данные
        self.player_stats = self._load_json(self.player_stats_file)
        self.season_stats = self._load_json(self.season_stats_file)
        self.teams_history = self._load_json(self.teams_history_file)
        self.weekly_stats = self._load_json(self.weekly_stats_file)
        
    def _load_json(self, file_path: str) -> Dict:
        """Загрузка данных из JSON файла
        
        Args:
            file_path (str): Путь к файлу
            
        Returns:
            Dict: Загруженные данные или пустой словарь
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            
            # Создаем базовую структуру файла
            base_structure = {
                'weeks': {},
                'players': {},
                'teams': {}
            }
            self._save_json(base_structure, file_path)
            return base_structure
            
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке файла {file_path}: {e}")
            return {}
            
    def _save_json(self, data: Dict, file_path: str) -> bool:
        """Сохранение данных в JSON файл
        
        Args:
            data (Dict): Данные для сохранения
            file_path (str): Путь к файлу
            
        Returns:
            bool: True если сохранение успешно, False в случае ошибки
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении файла {file_path}: {e}")
            return False
            
    def get_team_of_the_day(self, date: Optional[datetime] = None) -> Dict[str, List[Dict]]:
        """Получение команды дня
        
        Args:
            date (datetime, optional): Дата для получения статистики
            
        Returns:
            Dict[str, List[Dict]]: Словарь с игроками по позициям
        """
        try:
            # Получаем статистику за день
            stats = self.espn_service.get_daily_stats(date)
            if not stats:
                self.logger.error("Не удалось получить статистику")
                return {}
            
            # Группируем игроков по позициям
            players_by_position = self._group_players_by_position(stats)
            
            # Выбираем лучших игроков для каждой позиции
            team = {}
            for position, count in self.positions.items():
                team[position] = self._get_best_players(
                    players_by_position.get(position, []),
                    count
                )
            
            # Сохраняем команду в историю
            self._save_team_to_history(team, date)
            
            return team
            
        except Exception as e:
            self.logger.error(f"Ошибка при формировании команды дня: {e}")
            return {}
            
    def get_team_of_the_week(self, start_date: Optional[datetime] = None) -> Dict[str, List[Dict]]:
        """Получение команды недели
        
        Args:
            start_date (datetime, optional): Дата начала недели
            
        Returns:
            Dict[str, List[Dict]]: Словарь с игроками по позициям
        """
        try:
            if start_date is None:
                # Получаем начало текущей недели (понедельник)
                start_date = datetime.now()
                start_date = start_date - timedelta(days=start_date.weekday())
            
            # Получаем конец недели
            end_date = start_date + timedelta(days=6)
            
            # Формируем ключ недели
            week_key = f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"
            
            # Проверяем, есть ли уже данные за эту неделю
            if week_key in self.weekly_stats:
                return self.weekly_stats[week_key]
            
            # Собираем статистику за всю неделю
            weekly_stats = {}
            current_date = start_date
            while current_date <= end_date:
                daily_team = self.get_team_of_the_day(current_date)
                for position, players in daily_team.items():
                    if position not in weekly_stats:
                        weekly_stats[position] = {}
                    
                    for player in players:
                        player_id = str(player['id'])
                        if player_id not in weekly_stats[position]:
                            weekly_stats[position][player_id] = {
                                'id': player_id,
                                'name': player['fullName'],
                                'position': position,
                                'appearances': 0,
                                'total_points': 0
                            }
                        
                        weekly_stats[position][player_id]['appearances'] += 1
                        weekly_stats[position][player_id]['total_points'] += player['stats'][0]['points']
                
                current_date += timedelta(days=1)
            
            # Выбираем лучших игроков недели
            team_of_the_week = {}
            for position, count in self.positions.items():
                players = list(weekly_stats.get(position, {}).values())
                # Сортируем сначала по количеству появлений, потом по очкам
                players.sort(key=lambda x: (x['appearances'], x['total_points']), reverse=True)
                team_of_the_week[position] = players[:count]
            
            # Сохраняем результаты
            self.weekly_stats[week_key] = team_of_the_week
            self._save_json(self.weekly_stats, self.weekly_stats_file)
            
            return team_of_the_week
            
        except Exception as e:
            self.logger.error(f"Ошибка при формировании команды недели: {e}")
            return {}
            
    def _group_players_by_position(self, stats: Dict) -> Dict[str, List[Dict]]:
        """Группировка игроков по позициям
        
        Args:
            stats (Dict): Статистика игроков
            
        Returns:
            Dict[str, List[Dict]]: Словарь игроков по позициям
        """
        try:
            result = {}
            for player in stats.get('players', []):
                if 'defaultPositionId' not in player:
                    continue
                
                position = self._get_position_code(player['defaultPositionId'])
                if not position:
                    continue
                
                if position not in result:
                    result[position] = []
                
                # Получаем статистику игрока
                player_stats = next(
                    (stat for stat in player.get('stats', [])
                     if stat.get('statSourceId') == 0),  # Используем только официальную статистику
                    {}
                )
                
                # Формируем данные игрока
                player_data = {
                    'id': str(player['id']),
                    'fullName': player['fullName'],
                    'defaultPositionId': player['defaultPositionId'],
                    'stats': [player_stats] if player_stats else [],
                    'grade': 'common'  # Базовый грейд
                }
                
                result[position].append(player_data)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка при группировке игроков: {e}")
            return {}
            
    def _get_best_players(self, players: List[Dict], count: int) -> List[Dict]:
        """Выбор лучших игроков на позиции
        
        Args:
            players (List[Dict]): Список игроков
            count (int): Количество игроков для выбора
            
        Returns:
            List[Dict]: Список лучших игроков
        """
        try:
            # Фильтруем игроков без статистики
            valid_players = [
                p for p in players
                if p.get('stats') and p['stats'][0].get('points') is not None
            ]
            
            # Сортируем по очкам
            sorted_players = sorted(
                valid_players,
                key=lambda x: x['stats'][0].get('points', 0),
                reverse=True
            )
            
            return sorted_players[:count]
            
        except Exception as e:
            self.logger.error(f"Ошибка при выборе лучших игроков: {e}")
            return []
            
    def _get_position_code(self, position_id: int) -> Optional[str]:
        """Преобразование ID позиции в код
        
        Args:
            position_id (int): ID позиции
            
        Returns:
            Optional[str]: Код позиции или None
        """
        position_map = {
            1: 'C',
            2: 'LW',
            3: 'RW',
            4: 'D',
            5: 'G'
        }
        return position_map.get(position_id)
        
    def _save_team_to_history(self, team: Dict[str, List[Dict]], date: Optional[datetime] = None) -> None:
        """Сохранение команды в историю
        
        Args:
            team (Dict[str, List[Dict]]): Команда дня
            date (datetime, optional): Дата команды
        """
        try:
            if date is None:
                date = datetime.now()
            
            date_key = date.strftime('%Y-%m-%d')
            
            # Сохраняем в историю команд
            self.teams_history['teams'][date_key] = team
            self._save_json(self.teams_history, self.teams_history_file)
            
            # Обновляем статистику игроков
            if date_key not in self.player_stats['players']:
                self.player_stats['players'][date_key] = {}
            
            for position_players in team.values():
                for player in position_players:
                    player_id = str(player['id'])
                    self.player_stats['players'][date_key][player_id] = player
            
            self._save_json(self.player_stats, self.player_stats_file)
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении команды в историю: {e}")
            
    def update_player_grades(self) -> None:
        """Обновление грейдов игроков на основе статистики"""
        try:
            # Получаем текущую неделю
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            # Считаем появления в команде дня за неделю
            appearances = {}
            
            for date_key, day_data in self.player_stats.get('players', {}).items():
                try:
                    date = datetime.strptime(date_key, '%Y-%m-%d')
                    if start_of_week <= date <= end_of_week:
                        for player_id, player_data in day_data.items():
                            if player_id not in appearances:
                                appearances[player_id] = 0
                            appearances[player_id] += 1
                except ValueError:
                    continue
            
            # Обновляем грейды
            for player_id, count in appearances.items():
                grade = 'common'
                if count >= 5:
                    grade = 'legend'
                elif count >= 4:
                    grade = 'epic'
                elif count >= 3:
                    grade = 'rare'
                elif count >= 2:
                    grade = 'uncommon'
                
                # Обновляем грейд в статистике
                for day_data in self.player_stats.get('players', {}).values():
                    if player_id in day_data:
                        day_data[player_id]['grade'] = grade
            
            # Сохраняем обновленные данные
            self._save_json(self.player_stats, self.player_stats_file)
            
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении грейдов игроков: {e}")
