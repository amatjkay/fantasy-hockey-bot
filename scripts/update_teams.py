from datetime import datetime, timedelta
import json
import os
from src.utils.logger import setup_logger

logger = setup_logger('update_teams')

def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {file_path}: {e}")
        return None

def save_json(data, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка при сохранении файла {file_path}: {e}")

def get_missing_dates(existing_teams):
    """Получить список дат, для которых отсутствуют команды дня"""
    today = datetime.now().date()
    dates_to_process = []
    current_date = datetime.strptime(min(existing_teams.keys()), "%Y-%m-%d").date()
    
    while current_date <= today:
        date_str = current_date.strftime("%Y-%m-%d")
        if date_str not in existing_teams:
            dates_to_process.append(date_str)
        current_date += timedelta(days=1)
    
    return dates_to_process

def create_team_of_day(player_stats, date):
    """Создать команду дня на основе статистики игроков"""
    # Здесь логика выбора лучших игроков дня
    # TODO: Реализовать алгоритм выбора игроков
    pass

def create_team_of_week(daily_teams, week_end_date):
    """Создать команду недели на основе команд дня"""
    # Здесь логика формирования команды недели
    # TODO: Реализовать алгоритм выбора игроков недели
    pass

def main():
    # Загрузка необходимых данных
    player_stats = load_json('data/processed/player_stats.json')
    daily_teams = load_json('data/processed/daily_teams.json')
    weekly_teams = load_json('data/processed/weekly_team_stats.json')

    # Получение списка дат для обработки
    missing_dates = get_missing_dates(daily_teams)
    
    # Формирование команд дня
    for date in missing_dates:
        team_of_day = create_team_of_day(player_stats, date)
        daily_teams[date] = team_of_day
        logger.info(f"Создана команда дня для {date}")

    # Формирование команды недели
    today = datetime.now().date()
    last_week_end = today - timedelta(days=today.weekday() + 1)
    weekly_team = create_team_of_week(daily_teams, last_week_end)
    
    # Сохранение результатов
    save_json(daily_teams, 'data/processed/daily_teams.json')
    save_json(weekly_teams, 'data/processed/weekly_team_stats.json')

if __name__ == "__main__":
    main() 