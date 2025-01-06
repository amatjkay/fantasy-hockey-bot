import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
import pytz
from dotenv import load_dotenv
from src.utils.logging import setup_logging
from src.config import settings
from collections import defaultdict

# Загружаем переменные окружения
load_dotenv()

class ESPNService:
    """Сервис для работы с API ESPN"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.logger = logging.getLogger(__name__)
        
        # Загружаем настройки из .env
        self.season = settings.ESPN_API['season_id']
        self.league_id = settings.ESPN_API['league_id']
        self.season_start = datetime.strptime(
            settings.SEASON_START,
            '%Y-%m-%d'
        ).replace(tzinfo=settings.ESPN_TIMEZONE)
        
        # Формируем базовый URL
        self.base_url = settings.ESPN_API['BASE_URL']
        
        # Настраиваем заголовки
        self.headers = settings.ESPN_API['HEADERS'].copy()
        
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
            
            # Получаем scoring_period_id для следующего дня,
            # так как статистика доступна только на следующий день
            stats_date = date + timedelta(days=1)
            scoring_period_id = self.get_scoring_period_id(stats_date)
            
            # Параметры запроса
            params = {
                'scoringPeriodId': scoring_period_id,
                'view': 'kona_player_info'
            }
            
            # Получаем статистику всех игроков
            fantasy_filter = {
                'players': {
                    'filterSlotIds': {'value': [0,1,2,3,4,5,6]},  # ID всех позиций
                    'filterStatsForCurrentSeasonScoringPeriodId': {'value': [scoring_period_id]},
                    'limit': 1000,
                    'offset': 0,
                    'sortAppliedStatTotalForScoringPeriodId': {
                        'sortAsc': False,
                        'sortPriority': 1,
                        'value': scoring_period_id
                    }
                }
            }
            
            headers = self.headers.copy()
            headers['x-fantasy-filter'] = json.dumps(fantasy_filter)
            
            data = self._make_request(params, headers)
            if not data:
                self.logger.error("Не удалось получить статистику")
                return None
                
            self.logger.info(f"Получены данные: {json.dumps(data)[:1000]}...")
            
            return {
                'date': date.strftime('%Y-%m-%d'),  # Возвращаем исходную дату
                'players': data.get('players', [])
            }
            
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
            fantasy_filter = self._get_fantasy_filter(start_date, end_date)
            
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
            response = requests.request(
                'GET',
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
        days_since_start = (date - self.season_start).days
        
        # ID периода - количество дней с начала сезона + 1
        period_id = days_since_start + 1
        
        return period_id, int(self.season)

    def _get_week_start_date(self, date: Optional[datetime] = None) -> datetime:
        """Получение даты начала недели
        
        Args:
            date (datetime, optional): Дата для получения начала недели
            
        Returns:
            datetime: Дата начала недели
        """
        if date is None:
            date = datetime.now(pytz.timezone(settings.ESPN_TIMEZONE))
            
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
            if position_id in settings.PLAYER_POSITIONS:
                position = settings.PLAYER_POSITIONS[position_id]
                result[position].append(player)
        return dict(result)

    def get_scoring_period_id(self, date: datetime) -> int:
        """Получение ID периода подсчета очков для указанной даты

        Args:
            date (datetime): Дата для которой нужно получить ID периода

        Returns:
            int: ID периода подсчета очков
        """
        period_id, _ = self._get_scoring_period_id(date)
        return period_id

    def get_week_start_date(self, date: datetime) -> datetime:
        """Получение даты начала недели для указанной даты

        Args:
            date (datetime): Дата для которой нужно получить начало недели

        Returns:
            datetime: Дата начала недели
        """
        return self._get_week_start_date(date)

    def _get_fantasy_filter(self, start_date: datetime, end_date: datetime) -> Dict:
        """Создание фильтра для API ESPN

        Args:
            start_date (datetime): Начальная дата
            end_date (datetime): Конечная дата

        Returns:
            Dict: Фильтр для API
        """
        return {
            'players': {
                'filterSlotIds': {'value': [0,1,2,3,4,5,6]},
                'filterStatsForExternalIds': {
                    'value': [f"{self.season}{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"]
                },
                'limit': 1000,
                'offset': 0,
                'sortAppliedStatTotal': {'sortAsc': False, 'sortPriority': 1}
            }
        }
