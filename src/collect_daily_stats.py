"""Скрипт для сбора ежедневной статистики игроков."""

import json
import logging
import time
from datetime import datetime, timedelta
import requests
from utils.config import (
    get_api_url,
    API_HEADERS,
    PLAYER_STATS_FILE,
    LOG_FILE,
    LOG_FORMAT,
    LOG_LEVEL,
    SEASON_ID
)

# Настройка логирования
logging.basicConfig(
    filename=LOG_FILE,
    format=LOG_FORMAT,
    level=LOG_LEVEL
)
logger = logging.getLogger(__name__)

# Создаем сессию для сохранения cookies
session = requests.Session()
session.headers.update(API_HEADERS)

def fetch_player_data(scoring_period_id):
    """Получает данные игроков для указанного периода."""
    url = get_api_url(scoring_period_id)
    
    logger.info(f"Запрашиваю данные для периода {scoring_period_id}")
    logger.debug(f"URL: {url}")
    
    try:
        response = session.get(url, allow_redirects=False)
        if response.status_code == 302:
            logger.error("Получен редирект, проблема с аутентификацией")
            return None
            
        response.raise_for_status()
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        logger.debug(f"Response text: {response.text[:500]}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе данных: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при разборе JSON: {e}")
        logger.debug(f"Полученный текст: {response.text[:500]}")
        return None

def get_player_stats(scoring_period_id, retries=3):
    """Получает статистику игроков с повторными попытками."""
    for attempt in range(retries):
        data = fetch_player_data(scoring_period_id)
        if data:
            return process_player_data(data)
        logger.warning(f"Попытка {attempt + 1} из {retries} не удалась")
        if attempt < retries - 1:
            time.sleep(5)  # Пауза перед следующей попыткой
    return {}

def process_player_data(data):
    """Обрабатывает данные игроков из ответа API."""
    player_stats = {}
    
    if not isinstance(data, dict):
        logger.error(f"Неверный формат данных: {type(data)}")
        return player_stats
        
    entries = data.get('roster', {}).get('entries', [])
    
    for entry in entries:
        player = entry.get('player', {})
        player_id = str(player.get('id'))
        
        if not player_id:
            continue
            
        stats = player.get('stats', [])
        if not stats:
            continue
            
        # Берем статистику за текущий сезон
        current_stats = next(
            (s for s in stats if s.get('externalId') == SEASON_ID 
             and s.get('statSplitTypeId') == 0),
            {}
        )
        
        if not current_stats:
            continue
            
        player_stats[player_id] = {
            'name': player.get('fullName'),
            'position': player.get('defaultPositionId'),
            'team': player.get('proTeamId'),
            'stats': current_stats.get('stats', {}),
            'ratings': entry.get('ratings', {})
        }
        
        logger.info(f"Обработаны данные игрока: {player.get('fullName')}")
        
    return player_stats

def save_stats(stats):
    """Сохраняет статистику в файл."""
    try:
        with open(PLAYER_STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        logger.info(f"Статистика сохранена в {PLAYER_STATS_FILE}")
    except IOError as e:
        logger.error(f"Ошибка при сохранении статистики: {e}")

def main():
    """Основная функция для сбора статистики."""
    logger.info("Начинаю сбор статистики")
    
    # Собираем статистику за последние 90 дней
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    all_stats = {}
    
    # Перебираем все дни и собираем статистику
    current_date = start_date
    while current_date <= end_date:
        scoring_period_id = current_date.timetuple().tm_yday
        logger.info(f"Обрабатываю дату: {current_date.date()}, период: {scoring_period_id}")
        
        daily_stats = get_player_stats(scoring_period_id)
        if daily_stats:
            all_stats[str(scoring_period_id)] = daily_stats
            
        current_date += timedelta(days=1)
        time.sleep(1)  # Пауза между запросами
    
    save_stats(all_stats)
    logger.info("Сбор статистики завершен")

if __name__ == '__main__':
    main() 