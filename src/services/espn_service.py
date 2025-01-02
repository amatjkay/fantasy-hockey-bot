import requests
import logging
from datetime import datetime, timedelta
import pytz
import json
import os

class ESPNService:
    def __init__(self):
        self.base_url = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/nhl/seasons"
        self.logger = logging.getLogger(__name__)
        self.season_start_day = 4  # День начала сезона
        self.season_start_month = 10  # Месяц начала сезона
        
        # Фиксированный сезон 2024-25
        self.season = 2025
        self.league_id = "484910394"
        
        # Загружаем грейды игроков
        self.player_grades = self._load_player_grades()
        
        # Инициализируем сервис для работы с изображениями
        from src.services.image_service import ImageService
        self.image_service = ImageService()

    def _load_player_grades(self):
        """Загрузка грейдов игроков из файла статистики"""
        try:
            with open('data/processed/player_stats.json', 'r') as f:
                data = json.load(f)
                
            grades = {}
            for week_data in data.get('weeks', {}).values():
                for player_id, player_info in week_data.get('players', {}).items():
                    grades[player_id] = player_info.get('grade', 'common')
            
            return grades
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке грейдов игроков: {e}")
            return {}

    def update_player_grades(self):
        """Обновление грейдов игроков из файла статистики"""
        self.player_grades = self._load_player_grades()
        self.logger.info("Грейды игроков обновлены")

    def get_daily_stats(self, date):
        """Получение статистики за день
        
        Args:
            date (datetime): Дата для получения статистики
            
        Returns:
            dict: Словарь с данными статистики
        """
        try:
            # Получаем ID периода подсчета очков и сезон
            scoring_period_id, season = self._get_scoring_period_id(date)
            self.logger.info(f"Получаем статистику для периода {scoring_period_id}")
            
            # Получаем данные по полевым игрокам
            url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/{season}/segments/0/leagues/{self.league_id}"
            
            params = {
                'scoringPeriodId': scoring_period_id,
                'view': 'kona_player_info'
            }
            
            # Фильтр для получения только нужных игроков
            filter_json = {
                "players": {
                    "filterSlotIds": {"value": [0, 1, 2, 3, 4, 6]},
                    "filterStatsForCurrentSeasonScoringPeriodId": {"value": [scoring_period_id]},
                    "sortPercOwned": {"sortPriority": 3, "sortAsc": False},
                    "limit": 50,
                    "offset": 0,
                    "sortAppliedStatTotalForScoringPeriodId": {
                        "sortAsc": False,
                        "sortPriority": 1,
                        "value": scoring_period_id
                    },
                    "filterRanksForScoringPeriodIds": {"value": [scoring_period_id]},
                    "filterRanksForRankTypes": {"value": ["STANDARD"]}
                }
            }
            
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0',
                'x-fantasy-filter': json.dumps(filter_json)
            }
            
            self.logger.info(f"Отправляем запрос к API: {url}")
            self.logger.info(f"Параметры: {params}")
            self.logger.info(f"Заголовки: {headers}")
            
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            self.logger.info(f"Получен ответ от API: {response.status_code}")
            self.logger.info(f"Содержимое ответа: {json.dumps(data)[:1000]}...")  # Логируем только первую 1000 символов
            
            # Обрабатываем данные полевых игроков
            field_players = self._process_field_players(data, scoring_period_id)
            self.logger.info(f"Получены данные по полевым игрокам: {field_players}")
            
            # Получаем данные по вратарям
            goalies = self._process_goalies(date, scoring_period_id, season)
            self.logger.info(f"Получены данные по вратарям: {goalies}")
            
            result = {
                'players': field_players + goalies
            }
            
            self.logger.info(f"Итоговый результат: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении статистики: {e}", exc_info=True)
            return None

    def _process_goalies(self, date, scoring_period_id, season):
        """Обработка статистики вратарей
        
        Args:
            date (datetime): Дата для получения статистики
            scoring_period_id (int): ID периода подсчета очков
            season (int): Сезон
            
        Returns:
            list: Список вратарей с их статистикой
        """
        try:
            url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/{season}/segments/0/leagues/{self.league_id}"
            
            params = {
                'scoringPeriodId': scoring_period_id,
                'view': 'kona_player_info'
            }
            
            # Фильтр для получения только вратарей
            filter_json = {
                "players": {
                    "filterSlotIds": {"value": [5]},  # 5 - ID позиции вратаря
                    "filterStatsForCurrentSeasonScoringPeriodId": {"value": [scoring_period_id]},
                    "sortPercOwned": {"sortPriority": 3, "sortAsc": False},
                    "limit": 50,
                    "offset": 0,
                    "sortAppliedStatTotalForScoringPeriodId": {
                        "sortAsc": False,
                        "sortPriority": 1,
                        "value": scoring_period_id
                    },
                    "filterRanksForScoringPeriodIds": {"value": [scoring_period_id]},
                    "filterRanksForRankTypes": {"value": ["STANDARD"]}
                }
            }
            
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0',
                'x-fantasy-filter': json.dumps(filter_json)
            }
            
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            players = []
            for player_entry in data.get('players', []):
                player = player_entry.get('player', {})
                if not player:
                    continue
                
                stats = player.get('stats', [])
                period_stats = next(
                    (stat for stat in stats 
                     if stat.get('scoringPeriodId') == scoring_period_id 
                     and stat.get('statSourceId') == 0),
                    None
                )
                
                if not period_stats:
                    continue
                
                points = period_stats.get('appliedTotal', 0)
                stat_values = period_stats.get('stats', {})
                
                # Получаем процент отраженных бросков
                saves = stat_values.get('24', 0) if stat_values else 0  # Saves
                shots_against = stat_values.get('25', 0) if stat_values else 0  # Shots Against
                save_pct = round(saves / shots_against, 3) if shots_against > 0 else 0
                
                player_id = str(player.get('id'))
                processed_player = {
                    'id': player_id,
                    'fullName': player.get('fullName'),
                    'defaultPositionId': 5,  # Вратарь
                    'grade': self.player_grades.get(player_id, 'common'),
                    'stats': [{
                        'points': points,
                        'totalPoints': points,
                        'savePct': save_pct
                    }]
                }
                players.append(processed_player)
                self.logger.info(f"Добавлен вратарь: {processed_player}")
            
            return players
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении статистики вратарей: {e}")
            return []

    def get_weekly_stats(self, start_date=None):
        """Получение статистики за неделю
        
        Args:
            start_date (datetime, optional): Начальная дата недели.
            
        Returns:
            dict: Статистика игроков за неделю
        """
        if start_date is None:
            start_date = self._get_week_start_date()
        
        end_date = start_date + timedelta(days=6)
        
        try:
            params = {
                'dates': f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}",
                'limit': 100
            }
            
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0'
            }
            
            response = requests.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Преобразуем данные в нужный формат
            players = []
            for event in data.get('events', []):
                for competition in event.get('competitions', []):
                    for competitor in competition.get('competitors', []):
                        for athlete in competitor.get('statistics', []):
                            if athlete.get('type', {}).get('id') == 'overall':
                                for stat in athlete.get('stats', []):
                                    player = {
                                        'id': str(athlete.get('athlete', {}).get('id')),
                                        'fullName': athlete.get('athlete', {}).get('displayName'),
                                        'defaultPositionId': self._get_position_id(athlete.get('athlete', {}).get('position', {}).get('abbreviation')),
                                        'stats': [{
                                            'points': float(stat.get('value', 0)),
                                            'totalPoints': float(stat.get('value', 0)),
                                            'savePct': float(stat.get('savePct', 0))
                                        }]
                                    }
                                    players.append(player)
            
            return {'players': players}
            
        except requests.RequestException as e:
            self.logger.error(f"Ошибка при получении недельной статистики: {e}")
            return None

    def _get_position_id(self, position_abbr):
        """Преобразование аббревиатуры позиции в ID"""
        position_map = {
            'C': 1,
            'LW': 2,
            'RW': 3,
            'D': 4,
            'G': 5
        }
        return position_map.get(position_abbr)

    def _get_scoring_period_id(self, date):
        """Получение ID периода подсчета очков и сезона
        
        Args:
            date (datetime): Дата для получения ID
            
        Returns:
            tuple: (scoring_period_id, season)
        """
        try:
            self.logger.info("Расчет scoring_period_id:")
            self.logger.info(f"Входная дата: {date}")
            
            # Используем фиксированный сезон 2025
            season = 2025
            self.logger.info(f"Год сезона: {season}")
            
            # Начало сезона - 4 октября 2024 в 4 утра по восточному времени
            eastern_tz = pytz.timezone('US/Eastern')
            season_start = eastern_tz.localize(datetime(2024, 10, 4, 4, 0, 0))
            
            # Если дата в UTC, конвертируем её в восточное время
            if date.tzinfo == pytz.UTC:
                date = date.astimezone(eastern_tz)
            elif date.tzinfo is None:
                # Если дата без временной зоны, предполагаем что она в восточном времени
                date = eastern_tz.localize(date)
            
            # Рассчитываем количество дней с начала сезона
            days_since_start = (date - season_start).days + 1
            
            if days_since_start < 1:
                raise ValueError(f"Дата {date} находится до начала сезона {season_start}")
            
            scoring_period_id = days_since_start
            self.logger.info(f"Рассчитанный scoring_period_id: {scoring_period_id}")
            
            return scoring_period_id, season
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении scoring_period_id: {e}")
            raise

    def _get_week_start_date(self):
        """Получение даты начала текущей недели (понедельник)"""
        today = datetime.now(pytz.timezone('America/New_York'))
        return today - timedelta(days=today.weekday())

    def get_team_of_the_day(self, date):
        """Получение команды дня
        
        Args:
            date (datetime): Дата для получения команды
            
        Returns:
            list: Список игроков команды дня
        """
        try:
            # Получаем статистику за день
            stats = self.get_daily_stats(date)
            if not stats or 'players' not in stats:
                self.logger.error("Не удалось получить статистику")
                return []

            # Группируем игроков по позициям
            positions = {
                'C': [],
                'LW': [],
                'RW': [],
                'D': [],
                'G': []
            }

            for player in stats['players']:
                try:
                    player_id = player.get('id')
                    position_id = player.get('defaultPositionId')
                    position = self._get_position_code(position_id)
                    
                    if not position:
                        self.logger.warning(f"Нет позиции для игрока {player.get('fullName')}")
                        continue
                        
                    self.logger.info(f"Обработка игрока: {player.get('fullName')}, позиция: {position}")
                    
                    # Получаем статистику игрока
                    player_stats = player.get('stats', [])
                    if not player_stats:
                        continue
                        
                    points = player_stats[0].get('points', 0)
                    
                    player_info = {
                        'id': player_id,
                        'name': player.get('fullName'),
                        'position': position,
                        'grade': player.get('grade', 'common'),
                        'stats': player_stats
                    }
                    positions[position].append((points, player_info))
                    
                except Exception as e:
                    self.logger.error(f"Ошибка при обработке игрока: {e}")
                    continue

            # Выбираем лучших игроков для каждой позиции
            position_limits = {
                'C': 1,
                'LW': 1,
                'RW': 1,
                'D': 2,
                'G': 1
            }

            # Формируем итоговый список игроков
            result_players = []
            for position, limit in position_limits.items():
                self.logger.info(f"Игроки на позиции {position}: {positions[position]}")
                # Сортируем игроков по очкам и берем лучших
                sorted_players = sorted(positions[position], key=lambda x: x[0], reverse=True)
                result_players.extend(player_info for _, player_info in sorted_players[:limit])

            self.logger.info(f"Итоговый список игроков: {result_players}")
            return result_players

        except Exception as e:
            self.logger.error(f"Ошибка при получении команды дня: {e}", exc_info=True)
            return []

    def _get_position_code(self, position_id):
        """Получение кода позиции по ID
        
        Args:
            position_id (int): ID позиции
            
        Returns:
            str: Код позиции (C, LW, RW, D, G) или None
        """
        position_map = {
            1: 'C',   # Центральный нападающий
            2: 'LW',  # Левый нападающий
            3: 'RW',  # Правый нападающий
            4: 'D',   # Защитник
            5: 'G'    # Вратарь
        }
        return position_map.get(position_id)

    def get_players_by_position(self, position):
        players = []
        for player in self.players_data:
            # Проверяем точное совпадение позиции
            if player['position'].upper() == position.upper():
                players.append({
                    'name': f"{player['firstName']} {player['lastName']}",
                    'position': player['position']
                    # Убрали fantasy_points из вывода
                })
        return players

    def create_player_collage(self, players):
        """Создает коллаж из изображений игроков
        
        Args:
            players (list): Список игроков
            
        Returns:
            bool: True если коллаж успешно создан, False в случае ошибки
        """
        try:
            # Создаем директорию для сохранения коллажа если её нет
            os.makedirs("data/output", exist_ok=True)
            
            # Путь для сохранения коллажа
            output_path = "data/output/team_collage.png"
            
            # Создаем коллаж с помощью ImageService
            result = self.image_service.create_team_collage(players, output_path)
            
            if result:
                self.logger.info(f"Коллаж успешно создан и сохранен в {output_path}")
            else:
                self.logger.error("Не удалось создать коллаж")
                
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании коллажа: {e}")
            return False

    def _process_field_players(self, data, scoring_period_id):
        """Обработка статистики полевых игроков
        
        Args:
            data (dict): Данные от API
            scoring_period_id (int): ID периода подсчета очков
            
        Returns:
            list: Список полевых игроков с их статистикой
        """
        try:
            players = []
            for player_entry in data.get('players', []):
                player = player_entry.get('player', {})
                if not player:
                    continue
                
                player_id = str(player.get('id'))
                stats = player.get('stats', [])
                period_stats = next(
                    (stat for stat in stats 
                     if stat.get('scoringPeriodId') == scoring_period_id 
                     and stat.get('statSourceId') == 0),
                    None
                )
                
                if not period_stats:
                    continue
                
                points = period_stats.get('appliedTotal', 0)
                
                processed_player = {
                    'id': player_id,
                    'fullName': player.get('fullName'),
                    'defaultPositionId': player.get('defaultPositionId'),
                    'grade': self.player_grades.get(player_id, 'common'),
                    'stats': [{
                        'points': points,
                        'totalPoints': points
                    }]
                }
                players.append(processed_player)
                self.logger.info(f"Добавлен игрок: {processed_player}")
            
            return players
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке статистики полевых игроков: {e}")
            return []
