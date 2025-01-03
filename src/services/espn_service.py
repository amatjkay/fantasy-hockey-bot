import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
import pytz
from src.utils.logging import setup_logging
from src.config import (
    ESPN_BASE_URL,
    ESPN_HEADERS,
    SEASON,
    LEAGUE_ID,
    get_fantasy_filter,
    TIMEZONE
)
from collections import defaultdict

class ESPNService:
    """Сервис для работы с API ESPN"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/2025/segments/0/leagues/484910394"
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Cookie': f'SWID={os.getenv("ESPN_SWID")}; espn_s2={os.getenv("ESPN_S2")}',
            'x-fantasy-source': 'kona',
            'x-fantasy-platform': 'kona-PROD-6daa0c838b3e2ff0192c0d7d1d24be52e5053a91'
        }
        
    def get_daily_stats(self, date: Optional[datetime] = None) -> Optional[Dict]:
        """Получение статистики за день
        
        Args:
            date (datetime, optional): Дата для получения статистики
            
        Returns:
            Optional[Dict]: Статистика игроков или None в случае ошибки
        """
        try:
            if date is None:
                date = datetime.now()
            
            # Получаем фильтр для API
            fantasy_filter = get_fantasy_filter(date, date)
            
            # Параметры запроса
            params = {
                'scoringPeriodId': 92,  # Фиксированное значение
                'view': 'kona_player_info'
            }
            
            # Получаем статистику вратарей
            goalie_filter = fantasy_filter.copy()
            goalie_filter['players'].update({
                'filterSlotIds': {'value': [5]},  # ID позиции вратаря
                'limit': 50,
                'offset': 0,
                'sortPercOwned': {'sortPriority': 3, 'sortAsc': False},
                'filterRanksForRankTypes': {'value': ['STANDARD']}
            })
            
            headers = self.headers.copy()
            headers['X-Fantasy-Filter'] = json.dumps(goalie_filter)
            
            goalie_data = self._make_request(params, headers)
            all_players = []
            
            if goalie_data and 'players' in goalie_data:
                all_players.extend(goalie_data['players'])
            
            # Получаем статистику полевых игроков
            skater_filter = fantasy_filter.copy()
            skater_filter['players'].update({
                'filterSlotIds': {'value': [0,1,2,3,4,6]},  # ID позиций полевых игроков
                'limit': 50,
                'offset': 0,
                'sortPercOwned': {'sortPriority': 3, 'sortAsc': False},
                'filterRanksForRankTypes': {'value': ['STANDARD']}
            })
            
            headers['X-Fantasy-Filter'] = json.dumps(skater_filter)
            
            skater_data = self._make_request(params, headers)
            if skater_data and 'players' in skater_data:
                all_players.extend(skater_data['players'])
            
            return {'players': all_players} if all_players else None
            
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при получении статистики: {e}")
            return None
            
    def get_weekly_stats(self, date: datetime) -> Optional[Dict]:
        """Получение статистики за неделю
        
        Args:
            date (datetime): Дата начала недели
            
        Returns:
            Optional[Dict]: Статистика игроков или None в случае ошибки
        """
        try:
            # Получаем даты начала и конца недели
            start_date = self._get_week_start_date(date)
            end_date = start_date + timedelta(days=6)
            
            # Получаем фильтр для API
            fantasy_filter = get_fantasy_filter(start_date, end_date)
            
            # Параметры запроса
            params = {
                'scoringPeriodId': 92,
                'view': 'mStats,kona_player_info',
                'startDate': start_date.strftime('%Y%m%d'),
                'endDate': end_date.strftime('%Y%m%d')
            }
            
            # Заголовки запроса
            headers = self.headers.copy()
            headers['X-Fantasy-Filter'] = json.dumps(fantasy_filter)
            
            # Выполняем запрос
            return self._make_request(params, headers)
            
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при получении недельной статистики: {e}")
            return None
            
    def _make_request(self, params: Dict, headers: Dict) -> Optional[Dict]:
        """Выполнение запроса к API
        
        Args:
            params (Dict): Параметры запроса
            headers (Dict): Заголовки запроса
            
        Returns:
            Optional[Dict]: Ответ API или None в случае ошибки
        """
        try:
            # Формируем URL
            url = f"{self.base_url}?view={params['view']}&scoringPeriodId={params['scoringPeriodId']}"
            
            # Отключаем предупреждения о SSL
            import urllib3
            urllib3.disable_warnings()
            
            # Выполняем запрос
            response = requests.get(
                url,
                headers=headers,
                timeout=30,
                verify=False  # Отключаем проверку SSL
            )
            
            # Проверяем статус
            response.raise_for_status()
            
            # Пытаемся получить JSON
            try:
                data = response.json()
                self.logger.info(f"Получен ответ от API")
                return data
            except ValueError as e:
                self.logger.error(f"Ошибка при парсинге JSON: {e}")
                self.logger.error(f"Текст ответа: {response.text[:1000]}")  # Логируем только первую 1000 символов
                return None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка при запросе к API: {e}")
            return None

    def _get_scoring_period_id(self, date: datetime) -> Tuple[int, int]:
        """Получение ID периода подсчета очков
        
        Args:
            date (datetime): Дата для получения ID
            
        Returns:
            Tuple[int, int]: (ID периода, сезон)
        """
        # Начало сезона - 4 октября 2024
        season_start = datetime(2024, 10, 4, tzinfo=pytz.timezone(TIMEZONE))
        days_since_start = (date - season_start).days
        
        # ID периода - количество дней с начала сезона + 1
        period_id = days_since_start + 1
        
        return period_id, 2025

    def _get_week_start_date(self, date: Optional[datetime] = None) -> datetime:
        """Получение даты начала недели
        
        Args:
            date (datetime, optional): Дата для получения начала недели
            
        Returns:
            datetime: Дата начала недели
        """
        if date is None:
            date = datetime.now(pytz.timezone(TIMEZONE))
            
        # Получаем понедельник текущей недели
        days_to_monday = date.weekday()
        monday = date - timedelta(days=days_to_monday)
        
        return monday.replace(hour=0, minute=0, second=0, microsecond=0)

    def get_players_by_position(self, players: List[Dict]) -> Dict[str, List[Dict]]:
        """Группировка игроков по позициям

        Args:
            players (List[Dict]): Список игроков

        Returns:
            Dict[str, List[Dict]]: Словарь игроков по позициям
        """
        result = defaultdict(list)
        for player in players:
            position_id = player.get('defaultPositionId')
            if position_id in POSITION_MAPPING:
                position = POSITION_MAPPING[position_id]
                result[position].append(player)
        return dict(result)

    def get_scoring_period_id(self, date: datetime) -> int:
        """Получение ID периода подсчета очков для указанной даты

        Args:
            date (datetime): Дата для которой нужно получить ID периода

        Returns:
            int: ID периода подсчета очков
        """
        return self._get_scoring_period_id(date)

    def get_week_start_date(self, date: datetime) -> datetime:
        """Получение даты начала недели для указанной даты

        Args:
            date (datetime): Дата для которой нужно получить начало недели

        Returns:
            datetime: Дата начала недели
        """
        return self._get_week_start_date(date)
