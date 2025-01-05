from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ..config import settings
import time
import json

logger = logging.getLogger(__name__)

class StatsService:
    def __init__(self):
        self.session = self._create_session()
        self.base_url = settings.ESPN_API['BASE_URL']
        
    def _create_session(self) -> requests.Session:
        """Создает сессию с настроенным механизмом повторных попыток"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=settings.MAX_RETRIES,
            backoff_factor=settings.RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def _get_auth_headers(self) -> Dict:
        """Формирует заголовки для авторизации"""
        headers = settings.ESPN_API['HEADERS'].copy()
        headers.update({
            "x-fantasy-filter": self._build_fantasy_filter()
        })
        return headers
        
    def _build_fantasy_filter(self, scoring_period_id: Optional[int] = None) -> str:
        """Формирует фильтр для API ESPN"""
        filter_data = {
            "players": {
                "filterSlotIds": {
                    "value": [0,1,2,3,4,5,6]
                },
                "filterStatsForCurrentSeasonScoringPeriodId": {
                    "value": [scoring_period_id] if scoring_period_id else []
                },
                "sortPercOwned": {
                    "sortPriority": 3,
                    "sortAsc": False
                },
                "limit": 50,
                "offset": 0,
                "sortAppliedStatTotalForScoringPeriodId": {
                    "sortAsc": False,
                    "sortPriority": 1,
                    "value": scoring_period_id
                } if scoring_period_id else None,
                "filterRanksForScoringPeriodIds": {
                    "value": [scoring_period_id]
                } if scoring_period_id else None,
                "filterRanksForRankTypes": {
                    "value": ["STANDARD"]
                }
            }
        }
            
        return json.dumps(filter_data)
    
    def get_daily_stats(self, date: datetime) -> Optional[Dict]:
        """Получает статистику за день"""
        scoring_period_id = self._get_scoring_period_id(date)
        if not scoring_period_id:
            return None

        url = settings.ESPN_API['BASE_URL']
        headers = self._get_auth_headers()
        params = settings.ESPN_API['PARAMS'].copy()
        params['scoringPeriodId'] = scoring_period_id
        
        for _ in range(settings.ESPN_API['RETRY_COUNT']):
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=settings.ESPN_API['TIMEOUT']
                )
                response.raise_for_status()
                logger.info(f"Получен ответ от API: {response.text[:500]}...")  # Логируем первые 500 символов ответа
                data = response.json()
                return self._process_daily_stats(data, date)
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка при получении данных: {str(e)}")
                time.sleep(settings.ESPN_API['RETRY_DELAY'])
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка при парсинге JSON: {str(e)}")
                logger.error(f"Полученный ответ: {response.text[:500]}...")  # Логируем ответ при ошибке парсинга
                time.sleep(settings.ESPN_API['RETRY_DELAY'])
        
        return None
        
    def _process_daily_stats(self, data: Dict, date: datetime) -> Dict:
        """Обрабатывает статистику за день"""
        logger.info(f"Обработка данных: {json.dumps(data)[:500]}...")
        
        processed_data = {
            "date": date.strftime("%Y-%m-%d"),
            "players": []
        }
        
        for player_data in data.get("players", []):
            logger.info(f"Обработка игрока: {json.dumps(player_data)[:500]}...")
            player = player_data.get("player", {})
            
            processed_player = {
                "info": {
                    "id": str(player_data.get("id")),
                    "name": player.get("fullName", ""),
                    "primary_position": player.get("defaultPositionId"),
                    "team_id": str(player.get("proTeamId"))
                },
                "stats": {
                    "total_points": 0,
                    "goals": 0,
                    "assists": 0,
                    "shots": 0,
                    "saves": 0,
                    "goals_against": 0
                }
            }
            
            # Получаем статистику за нужный период
            if "stats" in player:
                for stat_set in player.get("stats", []):
                    if "appliedTotal" in stat_set:
                        processed_player["stats"].update({
                            "total_points": float(stat_set.get("appliedTotal", 0)),
                            "goals": float(stat_set.get("stats", {}).get("6", 0)),
                            "assists": float(stat_set.get("stats", {}).get("7", 0)),
                            "shots": float(stat_set.get("stats", {}).get("13", 0)),
                            "saves": float(stat_set.get("stats", {}).get("31", 0)),
                            "goals_against": float(stat_set.get("stats", {}).get("32", 0))
                        })
                        break
            
            processed_data["players"].append(processed_player)
            
        return processed_data
        
    def _extract_player_stats(self, player: Dict) -> Dict:
        """Извлекает статистику игрока"""
        stats = {
            "total_points": 0,
            "goals": 0,
            "assists": 0,
            "shots": 0,
            "saves": 0,
            "goals_against": 0
        }
        
        if "stats" in player:
            for stat_set in player["stats"]:
                if stat_set.get("scoringPeriodId") == self._get_current_scoring_period():
                    stats.update({
                        "total_points": stat_set.get("appliedTotal", 0),
                        "goals": stat_set.get("stats", {}).get("6", 0),
                        "assists": stat_set.get("stats", {}).get("7", 0),
                        "shots": stat_set.get("stats", {}).get("13", 0),
                        "saves": stat_set.get("stats", {}).get("31", 0),
                        "goals_against": stat_set.get("stats", {}).get("32", 0)
                    })
                    break
                    
        return stats
        
    def _get_scoring_period_id(self, date: datetime) -> Optional[int]:
        """Определяет scoring_period_id для даты"""
        season_start = datetime.strptime(settings.SEASON_START, '%Y-%m-%d')
        
        if date < season_start:
            logger.error(f"Дата {date} раньше начала сезона {season_start}")
            return None
            
        # Вычисляем количество дней с начала сезона
        days_since_start = (date - season_start).days
        
        # scoring_period_id начинается с SEASON_START_SCORING_PERIOD
        scoring_period_id = settings.SEASON_START_SCORING_PERIOD + days_since_start
        
        return scoring_period_id
        
    def _get_current_scoring_period(self) -> int:
        """Получает текущий scoring_period_id"""
        return self._get_scoring_period_id(datetime.now())
        
    def _validate_response(self, data: Dict) -> bool:
        """Проверяет корректность данных от API"""
        return "players" in data and isinstance(data["players"], list)