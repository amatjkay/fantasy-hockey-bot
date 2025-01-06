from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ..config import settings
import json
from .cache_service import CacheService
import pytz

logger = logging.getLogger(__name__)

class StatsService:
    def __init__(self):
        self.session = self._create_session()
        self.base_url = settings.ESPN_API['BASE_URL']
        self.cache = CacheService()
        
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
    
    def _get_auth_headers(self, scoring_period_id: Optional[int] = None) -> Dict:
        """Формирует заголовки для авторизации"""
        headers = settings.ESPN_API['HEADERS'].copy()
        
        if scoring_period_id:
            filter_data = {
                "players": {
                    "filterSlotIds": {"value": [0,1,2,3,4,5,6]},
                    "filterStatsForCurrentSeasonScoringPeriodId": {"value": [scoring_period_id]},
                    "limit": 50,
                    "sortAppliedStatTotalForScoringPeriodId": {
                        "sortAsc": False,
                        "sortPriority": 1,
                        "value": scoring_period_id
                    }
                }
            }
            headers["x-fantasy-filter"] = json.dumps(filter_data)
            
        return headers
        
    def get_daily_stats(self, date: datetime) -> Optional[Dict]:
        """
        Получает статистику за указанный день
        
        Args:
            date: Дата для получения статистики
            
        Returns:
            Dict со статистикой или None в случае ошибки
        """
        try:
            # Проверяем кэш
            cache_key = f"stats_{date.strftime('%Y-%m-%d')}"
            cached_data = self.cache.get_cached_data(cache_key)
            if cached_data:
                logger.info(f"Использованы кэшированные данные за {date.date()}")
                return cached_data
            
            # Получаем scoring_period_id
            scoring_period_id = self._get_scoring_period_id(date)
            if not scoring_period_id:
                logger.error(f"Не удалось определить scoring_period_id для {date.date()}")
                return None
            
            # Делаем запрос к API
            headers = self._get_auth_headers(scoring_period_id)
            response = self.session.get(
                self.base_url,
                headers=headers,
                params={"scoringPeriodId": scoring_period_id},
                timeout=settings.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            # Проверяем данные
            if not self._validate_response(data):
                logger.error("Получены некорректные данные от API")
                return None
            
            # Обрабатываем данные
            processed_data = self._process_daily_stats(data, date)
            
            # Сохраняем в кэш
            if processed_data and processed_data["players"]:
                self.cache.cache_data(cache_key, processed_data)
                logger.info(f"Данные за {date.date()} сохранены в кэш")
            
            return processed_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к API: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при разборе JSON: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {str(e)}")
            return None
    
    def _process_daily_stats(self, data: Dict, date: datetime) -> Dict:
        """Обрабатывает статистику за день"""
        processed_data = {
            "date": date.strftime("%Y-%m-%d"),
            "players": []
        }
        
        for player_data in data.get("players", []):
            try:
                player = player_data.get("player", {})
                if not player:
                    continue
                
                # Базовая информация об игроке
                player_info = {
                    "id": str(player.get("id")),
                    "name": player.get("fullName"),
                    "primary_position": player.get("defaultPositionId"),
                    "team_id": str(player.get("proTeamId"))
                }
                
                # Проверяем обязательные поля
                if not all(player_info.values()):
                    logger.warning(f"Пропущен игрок из-за отсутствия обязательных полей: {player_info}")
                    continue
                
                # Статистика игрока
                player_stats = self._extract_player_stats(player_data)
                
                processed_data["players"].append({
                    "info": player_info,
                    "stats": player_stats
                })
                
            except Exception as e:
                logger.error(f"Ошибка при обработке данных игрока: {str(e)}")
                continue
        
        return processed_data
    
    def _extract_player_stats(self, player_data: Dict) -> Dict:
        """Извлекает статистику игрока"""
        stats = {
            "total_points": 0,
            "goals": 0,
            "assists": 0,
            "shots": 0,
            "saves": 0,
            "goals_against": 0
        }
        
        try:
            if "stats" in player_data:
                for stat_set in player_data.get("stats", []):
                    if "appliedTotal" in stat_set:
                        raw_stats = stat_set.get("stats", {})
                        stats.update({
                            "total_points": float(stat_set.get("appliedTotal", 0)),
                            "goals": float(raw_stats.get("6", 0)),
                            "assists": float(raw_stats.get("7", 0)),
                            "shots": float(raw_stats.get("13", 0)),
                            "saves": float(raw_stats.get("31", 0)),
                            "goals_against": float(raw_stats.get("32", 0))
                        })
                        break
        except (ValueError, TypeError) as e:
            logger.error(f"Ошибка при извлечении статистики игрока: {str(e)}")
            
        return stats
    
    def _get_scoring_period_id(self, date: datetime) -> Optional[int]:
        """Определяет scoring_period_id для даты"""
        try:
            # Преобразуем дату начала сезона в UTC
            season_start = datetime.strptime(settings.SEASON_START, '%Y-%m-%d').replace(tzinfo=pytz.UTC)
            
            # Если дата без часового пояса, добавляем UTC
            if date.tzinfo is None:
                date = date.replace(tzinfo=pytz.UTC)
            
            if date < season_start:
                logger.error(f"Дата {date.date()} раньше начала сезона {season_start.date()}")
                return None
            
            days_since_start = (date - season_start).days
            scoring_period_id = settings.SEASON_START_SCORING_PERIOD + days_since_start
            
            return scoring_period_id
            
        except Exception as e:
            logger.error(f"Ошибка при вычислении scoring_period_id: {str(e)}")
            return None
    
    def _validate_response(self, data: Optional[Dict]) -> bool:
        """Проверяет корректность ответа от API"""
        if not data:
            return False
        
        if not isinstance(data, dict):
            return False
            
        if "players" not in data or not isinstance(data["players"], list):
            return False
            
        return True
    
    def update_player_stats(self, team: List[Dict], date: datetime, stats_file: str) -> None:
        """
        Обновляет статистику игроков и управляет их грейдами
        
        Args:
            team: Список игроков команды дня
            date: Дата статистики
            stats_file: Путь к файлу со статистикой
        """
        try:
            # Загружаем текущую статистику
            with open(stats_file, 'r') as f:
                stats = json.load(f)
            
            # Инициализируем структуру данных, если она отсутствует
            if "days" not in stats:
                stats["days"] = {}
            if "players" not in stats:
                stats["players"] = {}
            if "weekly_grades" not in stats:
                stats["weekly_grades"] = {}
            if "daily_appearances" not in stats:
                stats["daily_appearances"] = {}
            
            day_key = date.strftime('%Y-%m-%d')
            week_key = (date - timedelta(days=date.weekday())).strftime('%Y-%m-%d')
            
            # Проверяем, не обрабатывали ли мы уже эту дату
            if day_key in stats["daily_appearances"]:
                logger.info(f"Статистика за {day_key} уже обработана")
                return
            
            # Инициализируем статистику для текущего дня
            if day_key not in stats["days"]:
                stats["days"][day_key] = {
                    "C": [], "LW": [], "RW": [], "D": [], "G": []
                }
            
            # Инициализируем список появлений за день
            stats["daily_appearances"][day_key] = []
            
            # Обрабатываем каждого игрока
            for player in team:
                player_id = str(player["id"])
                position_id = player["defaultPositionId"]
                
                # Определяем позицию игрока
                position = self._get_position_code(position_id)
                if not position:
                    continue
                
                # Инициализируем данные игрока, если он новый
                if player_id not in stats["players"]:
                    stats["players"][player_id] = {
                        "name": player["fullName"],
                        "position": position,
                        "weekly_appearances": 0,
                        "total_points": 0
                    }
                
                # Проверяем, не началась ли новая неделя
                if week_key not in stats["weekly_grades"]:
                    stats["weekly_grades"][week_key] = {}
                    # Сбрасываем счетчики для всех игроков
                    for pid in stats["players"]:
                        stats["players"][pid]["weekly_appearances"] = 0
                
                # Обновляем статистику игрока
                player_stats = player["stats"][0]
                total_points = player_stats.get("points", 0)
                
                # Увеличиваем счетчик появлений за неделю
                stats["players"][player_id]["weekly_appearances"] += 1
                stats["players"][player_id]["total_points"] = total_points
                
                # Определяем грейд игрока
                appearances = stats["players"][player_id]["weekly_appearances"]
                grade = self._get_grade_by_appearances(appearances)
                
                # Добавляем игрока в статистику дня
                player_day_stats = {
                    "id": player_id,
                    "name": player["fullName"],
                    "grade": grade,
                    "stats": {
                        "total_points": total_points
                    },
                    "points": total_points
                }
                
                stats["days"][day_key][position].append(player_day_stats)
                stats["daily_appearances"][day_key].append(player_id)
            
            # Сохраняем обновленную статистику
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
                
            logger.info(f"Статистика за {day_key} успешно обновлена")
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении статистики: {str(e)}")
            raise
    
    def _get_position_code(self, position_id: int) -> Optional[str]:
        """Преобразует ID позиции в код"""
        position_map = {
            1: "C",   # Center
            2: "LW",  # Left Wing
            3: "RW",  # Right Wing
            4: "D",   # Defense
            5: "G"    # Goalie
        }
        return position_map.get(position_id)
    
    def _get_grade_by_appearances(self, appearances: int) -> str:
        """Определяет грейд игрока по количеству появлений за неделю"""
        grade_map = {
            1: "common",
            2: "uncommon",
            3: "rare",
            4: "epic",
            5: "legend"
        }
        return grade_map.get(appearances, "legend")