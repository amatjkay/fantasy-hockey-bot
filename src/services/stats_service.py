import json
import os
from datetime import datetime, timedelta
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
        
    def collect_stats(self, date: datetime) -> Optional[Dict]:
        """Сбор статистики за указанную дату
        
        Args:
            date (datetime): Дата для сбора статистики
            
        Returns:
            Optional[Dict]: Собранная статистика или None в случае ошибки
        """
        try:
            # Получаем статистику от ESPN
            stats = self.espn_service.get_daily_stats(date)
            if not stats:
                self.logger.error(f"Не удалось получить статистику за {date}")
                return None
                
            # Обновляем статистику игроков
            self.update_player_stats(stats['players'], date, self.player_stats_file)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Ошибка при сборе статистики: {e}")
            return None
            
    def collect_stats_range(self, start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """Сбор статистики за диапазон дат
        
        Args:
            start_date (datetime): Начальная дата
            end_date (datetime): Конечная дата
            
        Returns:
            Optional[Dict]: Собранная статистика или None в случае ошибки
        """
        try:
            all_stats = {'players': []}
            current_date = start_date
            
            while current_date <= end_date:
                stats = self.collect_stats(current_date)
                if stats and 'players' in stats:
                    all_stats['players'].extend(stats['players'])
                current_date += timedelta(days=1)
                
            return all_stats if all_stats['players'] else None
            
        except Exception as e:
            self.logger.error(f"Ошибка при сборе статистики за период: {e}")
            return None
            
    def update_player_stats(self, players: List[Dict], date: datetime, stats_file: str) -> None:
        """Обновление статистики игроков
        
        Args:
            players (List[Dict]): Список игроков с их статистикой
            date (datetime): Дата статистики
            stats_file (str): Путь к файлу статистики
        """
        try:
            # Загружаем текущую статистику
            stats = self._load_json(stats_file)
            
            # Получаем ключ недели
            week_start = date - timedelta(days=date.weekday())
            week_end = week_start + timedelta(days=6)
            week_key = f"{week_start.strftime('%Y-%m-%d')}_{week_end.strftime('%Y-%m-%d')}"
            
            # Создаем структуру для недели если её нет
            if week_key not in stats['weeks']:
                stats['weeks'][week_key] = {
                    'start_date': week_start.strftime('%Y-%m-%d'),
                    'end_date': week_end.strftime('%Y-%m-%d'),
                    'players': []
                }
                
            # Обновляем статистику игроков
            for player in players:
                player_id = str(player['id'])
                player_stats = next(
                    (p for p in stats['weeks'][week_key]['players'] if str(p['id']) == player_id),
                    None
                )
                
                if player_stats:
                    # Обновляем существующую статистику
                    player_stats['appearances'] += 1
                    player_stats['total_points'] += player['stats'][0]['points']
                else:
                    # Добавляем нового игрока
                    stats['weeks'][week_key]['players'].append({
                        'id': player_id,
                        'name': player['fullName'],
                        'position': self._get_position_code(player['defaultPositionId']),
                        'appearances': 1,
                        'total_points': player['stats'][0]['points']
                    })
                    
            # Обновляем грейды игроков
            self.update_player_grades(stats['weeks'][week_key]['players'])
            
            # Сохраняем обновленную статистику
            self._save_json(stats, stats_file)
            
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении статистики игроков: {e}")
            
    def update_player_grades(self, players: List[Dict]) -> None:
        """Обновление грейдов игроков
        
        Args:
            players (List[Dict]): Список игроков для обновления грейдов
        """
        try:
            for player in players:
                # Рассчитываем грейд на основе очков и появлений
                avg_points = player['total_points'] / player['appearances']
                
                # Определяем грейд
                if avg_points >= 20:
                    player['grade'] = 'legendary'
                elif avg_points >= 15:
                    player['grade'] = 'epic'
                elif avg_points >= 10:
                    player['grade'] = 'rare'
                else:
                    player['grade'] = 'common'
                    
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении грейдов игроков: {e}")
            
    def _get_position_code(self, position_id: int) -> Optional[str]:
        """Получение кода позиции по ID
        
        Args:
            position_id (int): ID позиции
            
        Returns:
            Optional[str]: Код позиции или None
        """
        return POSITION_MAPPING.get(position_id)
            
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
            # Сортируем игроков по очкам
            sorted_players = sorted(
                players,
                key=lambda x: x['stats'][0]['points'] if x['stats'] else 0,
                reverse=True
            )
            
            return sorted_players[:count]
            
        except Exception as e:
            self.logger.error(f"Ошибка при выборе лучших игроков: {e}")
            return []
            
    def _save_team_to_history(self, team: Dict[str, List[Dict]], date: datetime) -> None:
        """Сохранение команды в историю
        
        Args:
            team (Dict[str, List[Dict]]): Команда для сохранения
            date (datetime): Дата команды
        """
        try:
            date_key = date.strftime('%Y-%m-%d')
            self.teams_history[date_key] = team
            self._save_json(self.teams_history, self.teams_history_file)
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении команды в историю: {e}")
