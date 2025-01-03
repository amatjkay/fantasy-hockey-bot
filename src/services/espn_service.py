import json
import logging
import os
import urllib3
from datetime import datetime
from typing import Dict, List, Optional
import requests
from src.utils.logging import setup_logging
from src.config import (
    ESPN_BASE_URL,
    ESPN_HEADERS,
    SEASON,
    LEAGUE_ID,
    get_fantasy_filter
)

class ESPNService:
    """Сервис для работы с API ESPN"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.logger = logging.getLogger(__name__)
        self.base_url = 'https://fantasy.espn.com/apis/v3/games/fhl/seasons/2024/segments/0/leagues/1'
        self.default_headers = {
            'Cookie': f'SWID={os.getenv("ESPN_SWID")}; espn_s2={os.getenv("ESPN_S2")}'
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

    def get_stats(self, date: datetime) -> Optional[Dict]:
        """Получение статистики за указанную дату
        
        Args:
            date (datetime): Дата, за которую нужно получить статистику
            
        Returns:
            Optional[Dict]: Статистика или None в случае ошибки
        """
        # Параметры запроса
        params = {
            'view': 'kona_player_info',
            'scoringPeriodId': 92  # Фиксированное значение для всех запросов
        }
        
        # Заголовки запроса
        headers = self.default_headers.copy()
        headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'x-fantasy-filter': json.dumps({
                'players': {
                    'filterStatsForExternalIds': {
                        'value': [date.year]
                    },
                    'filterSlotIds': {
                        'value': [0, 1, 2, 3, 4, 5, 6]  # ID слотов для всех позиций
                    },
                    'filterStatsForSourceIds': {
                        'value': [0, 1]  # Источники статистики
                    }
                }
            }),
            'x-fantasy-platform': 'kona-PROD-6daa0c838b3e2ff0192c0d7d1d24be52e5053a91',
            'x-fantasy-source': 'kona'
        })
        
        # Выполняем запрос
        return self._make_request(params, headers)
