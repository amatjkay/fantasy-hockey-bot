import sys
import os
import logging
import argparse
from datetime import datetime
import shutil

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.espn_service import ESPNService

def setup_logging():
    """Настройка логирования"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Настраиваем формат логов
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Создаем файл лога с текущей датой
    log_file = os.path.join(log_dir, f"season_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def clear_stats():
    """Очистка текущих результатов"""
    files_to_clear = [
        'data/processed/player_stats.json',
        'data/processed/season_stats.json',
        'data/processed/teams_history.json',
        'data/processed/weekly_team_stats.json'
    ]
    
    for file_path in files_to_clear:
        try:
            if os.path.exists(file_path):
                # Создаем бэкап файла
                backup_path = f"{file_path}.bak"
                shutil.copy2(file_path, backup_path)
                # Удаляем файл
                os.remove(file_path)
                logging.info(f"Файл {file_path} очищен (создан бэкап)")
        except Exception as e:
            logging.error(f"Ошибка при очистке файла {file_path}: {e}")

def parse_args():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description='Сбор статистики за сезон')
    parser.add_argument('--date', type=str, help='Дата для сбора статистики (YYYY-MM-DD)')
    parser.add_argument('--clear', action='store_true', help='Очистить текущие результаты')
    return parser.parse_args()

def main():
    """Основная функция для сбора статистики за сезон"""
    # Настраиваем логирование
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Парсим аргументы
        args = parse_args()
        
        # Очищаем результаты если нужно
        if args.clear:
            logger.info("Очистка текущих результатов...")
            clear_stats()
        
        logger.info("Начинаем сбор статистики за сезон")
        
        # Инициализируем сервис ESPN
        espn_service = ESPNService()
        
        # Подготавливаем дату если она указана
        target_date = None
        if args.date:
            try:
                target_date = datetime.strptime(args.date, '%Y-%m-%d')
                logger.info(f"Сбор статистики за конкретную дату: {args.date}")
            except ValueError as e:
                logger.error(f"Неверный формат даты: {e}")
                sys.exit(1)
        
        # Получаем статистику за сезон
        stats = espn_service.get_season_stats(target_date)
        
        if stats:
            logger.info("Статистика за сезон успешно собрана и сохранена")
            
            # Выводим краткую сводку
            total_days = len(stats['days'])
            total_players = len(stats['players'])
            logger.info(f"Собрана статистика за {total_days} дней")
            logger.info(f"Всего игроков: {total_players}")
        else:
            logger.error("Не удалось собрать статистику за сезон")
        
    except Exception as e:
        logger.error(f"Произошла ошибка при сборе статистики: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 