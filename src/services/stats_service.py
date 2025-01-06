from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ..config import settings
from ..config.settings import PLAYER_POSITIONS
import json
from .cache_service import CacheService
import pytz
from collections import defaultdict

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
                
            logger.info(f"Получен scoring_period_id {scoring_period_id} для даты {date.date()}")
            
            # Делаем запрос к API
            headers = self._get_auth_headers(scoring_period_id)
            params = {
                "scoringPeriodId": scoring_period_id,
                "view": ["kona_player_info", "mStats", "mRoster"]
            }
            
            logger.info(f"URL запроса: {self.base_url}")
            logger.info(f"Заголовки запроса: {headers}")
            logger.info(f"Параметры запроса: {params}")
            
            response = self.session.get(
                self.base_url,
                headers=headers,
                params=params,
                timeout=settings.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Получен ответ от API: {data}")
            
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
            logger.error(f"Ошибка при запросе к API: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при разборе JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            return None
    
    def _process_daily_stats(self, data: Dict, date: datetime) -> Dict:
        """Обрабатывает статистику за день"""
        processed_data = {
            "date": date.strftime("%Y-%m-%d"),
            "players": []
        }
        
        logger.info(f"Начинаем обработку данных от API. Количество игроков: {len(data.get('players', []))}")
        
        for player_data in data.get("players", []):
            try:
                # Получаем базовую информацию об игроке
                player = player_data.get("player", {})
                if not player:
                    logger.warning("Пропущен игрок: нет данных player")
                    continue
                    
                position_id = player.get("defaultPositionId")
                if position_id not in settings.PLAYER_POSITIONS:
                    logger.warning(f"Пропущен игрок: неизвестная позиция {position_id}")
                    continue
                    
                # Базовая информация об игроке
                player_info = {
                    "id": str(player.get("id")),
                    "name": player.get("fullName"),
                    "primary_position": position_id,
                    "team_id": str(player.get("proTeamId"))
                }
                
                # Проверяем обязательные поля
                if not all(player_info.values()):
                    logger.warning(f"Пропущен игрок из-за отсутствия обязательных полей: {player_info}")
                    continue
                
                # Получаем очки
                total_points = 0
                stats_found = False
                for stat_set in player_data.get("stats", []):
                    if "appliedTotal" in stat_set:
                        total_points = float(stat_set.get("appliedTotal", 0))
                        stats_found = True
                        break
                
                if not stats_found:
                    logger.warning(f"Пропущен игрок {player_info['name']}: нет данных о статистике")
                    continue
                
                # Добавляем игрока только если у него есть очки
                if total_points > 0:
                    processed_data["players"].append({
                        "info": player_info,
                        "stats": {
                            "total_points": total_points
                        }
                    })
                    logger.info(f"Добавлен игрок {player_info['name']} ({settings.PLAYER_POSITIONS[position_id]}) с {total_points} очками")
                else:
                    logger.debug(f"Пропущен игрок {player_info['name']}: нет очков")
                
            except Exception as e:
                logger.error(f"Ошибка при обработке данных игрока: {str(e)}")
                continue
        
        logger.info(f"Обработка завершена. Добавлено игроков: {len(processed_data['players'])}")
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
            season_start = datetime.strptime(settings.SEASON_START, '%Y-%m-%d')
            
            # Если дата с часовым поясом, убираем его
            if date.tzinfo is not None:
                date = date.replace(tzinfo=None)
            
            if date < season_start:
                logger.error(f"Дата {date.date()} раньше начала сезона {season_start.date()}")
                return None
                
            # Вычисляем количество дней с начала сезона
            days_from_start = (date - season_start).days
            
            # Получаем scoring_period_id
            scoring_period_id = settings.SEASON_START_SCORING_PERIOD + days_from_start
            
            return scoring_period_id
            
        except Exception as e:
            logger.error(f"Ошибка при определении scoring_period_id: {e}")
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
        
    def _get_week_key(self, date: datetime) -> str:
        """
        Получает ключ недели для даты
        
        Args:
            date: Дата
            
        Returns:
            str: Ключ недели в формате YYYY-WW
        """
        # Получаем номер недели
        week_number = date.isocalendar()[1]
        
        # Формируем ключ
        return f"{date.year}-{week_number:02d}"
        
    def load_stats(self) -> Optional[Dict]:
        """
        Загружает статистику из файла
        
        Returns:
            Dict со статистикой или None в случае ошибки
        """
        try:
            stats_file = settings.STATS_FILE
            if not stats_file.exists():
                logger.error(f"Файл статистики не найден: {stats_file}")
                return None
            
            with open(stats_file, 'r') as f:
                stats = json.load(f)
            
            return stats
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при разборе JSON: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при загрузке статистики: {str(e)}")
            return None
            
    def save_stats(self, stats: Dict) -> bool:
        """
        Сохраняет статистику в файл
        
        Args:
            stats: Статистика для сохранения
            
        Returns:
            bool: True если сохранение успешно, False в случае ошибки
        """
        try:
            stats_file = settings.STATS_FILE
            
            # Создаем директорию, если её нет
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Сохраняем статистику
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
                
            logger.info("Статистика успешно сохранена")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении статистики: {str(e)}")
            return False
            
    def get_team_of_the_week(self, start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """
        Формирует команду недели на основе статистики за указанный период
        
        Args:
            start_date: Начальная дата периода
            end_date: Конечная дата периода
            
        Returns:
            Dict с командой недели или None в случае ошибки
        """
        try:
            # Проверяем, что даты не раньше начала сезона
            season_start = datetime.strptime(settings.SEASON_START, '%Y-%m-%d')
            if start_date.replace(tzinfo=None) < season_start:
                start_date = season_start
                
            # Собираем статистику за каждый день недели
            weekly_players = defaultdict(lambda: {
                "info": None,
                "stats": {
                    "total_points": 0
                }
            })
            
            current_date = start_date
            while current_date <= end_date:
                daily_stats = self.get_daily_stats(current_date)
                if daily_stats and "players" in daily_stats:
                    for player in daily_stats["players"]:
                        player_id = player["info"]["id"]
                        if not weekly_players[player_id]["info"]:
                            weekly_players[player_id]["info"] = player["info"]
                        weekly_players[player_id]["stats"]["total_points"] += player["stats"]["total_points"]
                current_date += timedelta(days=1)
                
            # Преобразуем в список игроков
            players = [
                {
                    "info": data["info"],
                    "stats": data["stats"]
                }
                for player_id, data in weekly_players.items()
                if data["info"] is not None and data["stats"]["total_points"] > 0
            ]
            
            if not players:
                logger.error(f"Нет данных за период с {start_date.date()} по {end_date.date()}")
                return None
                
            return {
                "date": f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}",
                "players": players
            }
            
        except Exception as e:
            logger.error(f"Ошибка при формировании команды недели: {e}")
            return None
    
    def update_player_stats(self, team: Dict, date: datetime) -> None:
        """Обновляет статистику игрока"""
        stats = self.load_stats()
        
        # Получаем ключ недели
        week_key = self._get_week_key(date)
        
        # Инициализируем структуру, если её нет
        if "days" not in stats:
            stats["days"] = {}
        if "players" not in stats:
            stats["players"] = {}
            
        # Добавляем статистику за день
        date_str = date.strftime("%Y-%m-%d")
        if date_str not in stats["days"]:
            stats["days"][date_str] = team
            
        # Обновляем статистику игроков
        for position, player in team.items():
            player_id = player["info"]["id"]
            
            if player_id not in stats["players"]:
                stats["players"][player_id] = {
                    "info": player["info"],
                    "appearances": [],
                    "total_points": 0
                }
                
            # Добавляем появление в команде дня
            if date_str not in stats["players"][player_id]["appearances"]:
                stats["players"][player_id]["appearances"].append(date_str)
                
            # Обновляем общие очки
            stats["players"][player_id]["total_points"] += player["stats"]["total_points"]
            
        # Сохраняем обновленную статистику
        self.save_stats(stats)
        
    def collect_season_stats(self, start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """
        Собирает статистику за указанный период
        
        Args:
            start_date: Начальная дата периода
            end_date: Конечная дата периода
            
        Returns:
            Dict со статистикой или None в случае ошибки
        """
        try:
            logger = logging.getLogger(__name__)
            logger.info(f"Начинаем сбор статистики за период с {start_date.date()} по {end_date.date()}")
            
            stats = {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "total_days": 0,
                "days": {}
            }
            
            current_date = start_date
            while current_date <= end_date:
                logger.info(f"Обработка даты: {current_date.date()}")
                
                # Получаем статистику за день
                daily_stats = self.get_daily_stats(current_date)
                if daily_stats and daily_stats["players"]:
                    date_str = current_date.strftime("%Y-%m-%d")
                    stats["days"][date_str] = daily_stats
                    stats["total_days"] += 1
                    logger.info(f"Получена статистика за {date_str}, игроков: {len(daily_stats['players'])}")
                else:
                    logger.warning(f"Нет данных за {current_date.date()}")
                
                current_date += timedelta(days=1)
            
            logger.info(f"Сбор статистики завершен. Обработано дней: {stats['total_days']}")
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка при сборе статистики: {str(e)}")
            return None