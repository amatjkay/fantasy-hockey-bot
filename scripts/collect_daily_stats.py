"""Скрипт для сбора ежедневной статистики игроков."""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.config.settings import (
    ESPN_API,
    PLAYER_STATS_FILE,
    API_URL_TEMPLATE,
    ESPN_TIMEZONE,
    load_env_vars
)
from src.utils.logger import setup_logging
from src.utils.helpers import get_previous_week_dates, get_week_key
import json
import logging
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def get_espn_data(url, cookies):
    """Получение данных от ESPN API
    
    Args:
        url (str): URL для запроса
        cookies (dict): Куки для авторизации
        
    Returns:
        dict: Данные от API или None в случае ошибки
    """
    try:
        logging.info(f"Отправляю ��апрос к ESPN API: {url}")
        logging.debug(f"Cookies: {cookies}")
        
        response = requests.get(
            url, 
            cookies=cookies,
            headers=ESPN_API['HEADERS'],
            timeout=ESPN_API['TIMEOUT']
        )
        
        logging.info(f"Получен ответ от ESPN API. Статус: {response.status_code}")
        logging.debug(f"Заголовки ответа: {dict(response.headers)}")
            
        response.raise_for_status()
        data = response.json()
        
        logging.info("Данные успешно получены и распарсены")
        
        # Анализируем структуру данных
        if isinstance(data, dict):
            logging.info("Структура данных:")
            for key, value in data.items():
                if isinstance(value, list):
                    logging.info(f"- {key}: список из {len(value)} элементов")
                    if value:
                        logging.info(f"  Пример первого элемента: {list(value[0].keys())}")
                elif isinstance(value, dict):
                    logging.info(f"- {key}: словарь с ключами {list(value.keys())}")
                else:
                    logging.info(f"- {key}: {type(value)}")
        
        return data
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе к ESPN API: {str(e)}")
        if hasattr(e.response, 'text'):
            logging.error(f"Текст ответа: {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка при разборе JSON: {str(e)}")
        logging.error(f"Текст ответа: {response.text}")
        return None

def process_player_stats(data, scoring_period_id):
    """Обработка статистики игроков
    
    Args:
        data (dict): Данные от ESPN API
        scoring_period_id (int): Текущий период подсчета очков
        
    Returns:
        dict: Обработанная статистика игроков
    """
    players = {}
    
    try:
        logging.info("Начинаю обработку данных игроков")
        
        players_data = data.get('players', [])
        logging.info(f"Найдено {len(players_data)} игроков в данных")
        logging.info(f"Обрабатываю статистику за период: {scoring_period_id}")
        
        for player_entry in players_data:
            try:
                player = player_entry.get('player', {})
                if not player:
                    logging.warning("Пропускаю запись без данных игрока")
                    continue
                
                player_id = str(player.get('id'))
                if not player_id:
                    logging.warning("Пропускаю игрока без ID")
                    continue
                
                name = player.get('fullName', 'Unknown')
                logging.debug(f"Обрабатываю игрока {name} ({player_id})")
                
                # Определяем основную позицию игрока
                default_position_id = player.get('defaultPositionId')
                eligible_slots = player.get('eligibleSlots', [])
                
                logging.debug(f"Позиции игрока {name}: defaultPositionId={default_position_id}, eligibleSlots={eligible_slots}")
                
                # Определяем позицию
                if default_position_id == 1:  # Forward
                    # Для форвардов берем только одну позицию в порядке приоритета
                    if 0 in eligible_slots:  # C
                        primary_position = 'C'
                    elif 1 in eligible_slots:  # LW
                        primary_position = 'LW'
                    elif 2 in eligible_slots:  # RW
                        primary_position = 'RW'
                    else:
                        primary_position = 'F'  # Общая позиция форварда если нет конкретной
                elif default_position_id == 4:  # Defense
                    primary_position = 'D'
                elif default_position_id == 5:  # Goalie
                    primary_position = 'G'
                else:
                    primary_position = None
                
                if not primary_position:
                    logging.debug(f"Пропускаю игрока {name} - не определена позиция")
                    continue
                
                logging.debug(f"Позиция игрока {name}: {primary_position}")
                
                player_info = {
                    'name': name,
                    'positions': [primary_position],
                    'total_points': 0,
                    'appearances': 0,
                    'grade': 'common'
                }
                
                # Считаем очки за текущий период
                stats = player.get('stats', [])
                logging.debug(f"Статистика игрока {name}: {stats}")
                
                for stat in stats:
                    if not isinstance(stat, dict):
                        continue
                        
                    stat_period = stat.get('scoringPeriodId', 0)
                    points = stat.get('appliedTotal', 0)
                    logging.debug(f"Период: {stat_period}, Очки: {points}")
                    
                    if stat_period == scoring_period_id and points > 0:
                        player_info['total_points'] = points
                        player_info['appearances'] = 1
                        break
                
                # Пропускаем игроков без очков
                if player_info['total_points'] <= 0:
                    logging.debug(f"Пропускаю игрока {name} - нет очков")
                    continue
                
                logging.debug(f"Информация об игроке {name}: {player_info}")
                players[player_id] = player_info
                
            except Exception as e:
                logging.error(f"Ошибка при обработке игрока: {str(e)}")
                continue
        
        logging.info(f"Обработано {len(players)} игроков")
        return players
        
    except Exception as e:
        logging.error(f"Ошибка при обработке статистики игроков: {str(e)}")
        logging.exception("Полный стек ошибки:")
        return {}

def update_player_stats(players, week_key):
    """Обновление файла статистики игроков
    
    Args:
        players (dict): Новые данные о игрокам
        week_key (str): Ключ недели
        
    Returns:
        bool: True если обновление успешно, False в противном случае
    """
    try:
        # Создаем структуру данных если файл не существует
        if not os.path.exists(PLAYER_STATS_FILE):
            data = {"weeks": {}}
        else:
            with open(PLAYER_STATS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        # Добавляем или обновляем данные за неделю
        if week_key not in data["weeks"]:
            data["weeks"][week_key] = {"players": {}}
        
        # Обновляем статистику игроков
        for player_id, player_info in players.items():
            if player_id not in data["weeks"][week_key]["players"]:
                data["weeks"][week_key]["players"][player_id] = player_info
            else:
                current_info = data["weeks"][week_key]["players"][player_id]
                # Обновляем только если новые очки больше
                if player_info['total_points'] > current_info.get('total_points', 0):
                    current_info.update(player_info)
        
        # Сохраняем обновленные данные
        with open(PLAYER_STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logging.info(f"Файл статистики успешно обновлен: {PLAYER_STATS_FILE}")
        return True
    except Exception as e:
        logging.error(f"Ошибка при обновлении файла статистики: {str(e)}")
        return False

def main():
    """Основная функция скрипта"""
    try:
        # Проверяем переменные окружения
        env_vars = load_env_vars()
        
        # Получаем даты предыдущей недели
        previous_tuesday, previous_monday = get_previous_week_dates()
        week_key = get_week_key(previous_tuesday, previous_monday)
        
        # Определяем текущий период подсчета очков
        # Это количество дней с начала сезона
        days_from_start = (datetime.now(ESPN_TIMEZONE).date() - ESPN_API['SEASON_START_DATE'].date()).days
        scoring_period_id = ESPN_API['SEASON_START_SCORING_PERIOD_ID'] + days_from_start
        
        logging.info(f"Текущий период подсчета очков: {scoring_period_id}")
        
        # Формируем URL и куки для запроса
        url = API_URL_TEMPLATE.format(
            league_id=ESPN_API['LEAGUE_ID'],
            scoring_period_id=scoring_period_id
        )
        cookies = {
            'SWID': env_vars['ESPN_SWID'],
            'espn_s2': env_vars['ESPN_S2']
        }
        
        # Получаем данные от ESPN
        data = get_espn_data(url, cookies)
        if not data:
            logging.error("Не удалось получить данные от ESPN API")
            return
            
        # Обрабатываем статистику игроков
        players = process_player_stats(data, scoring_period_id)
        if not players:
            logging.error("Не удалось обработать статистику игроков")
            return
            
        # Обновляем файл статистики
        if not update_player_stats(players, week_key):
            logging.error("Не удалось обновить файл статистики")
            return
            
        logging.info("Сбор статистики успешно завершен")
        
    except Exception as e:
        logging.error(f"Ошибка при выполнении скрипта: {str(e)}")
        raise

if __name__ == "__main__":
    # Настраиваем логирование
    setup_logging()
    
    # Запус��аем основную функцию
    main() 