import os
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
root_dir = str(Path(__file__).parent.parent)
sys.path.append(root_dir)

from src.services.stats_service import StatsService
from src.services.image_service import ImageService
from src.services.telegram_service import TelegramService
from config.settings import SEASON_START

def main():
    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    try:
        # Инициализируем сервисы
        stats_service = StatsService()
        image_service = ImageService()
        telegram_service = TelegramService()

        # Получаем текущую дату
        current_date = datetime.now()
        
        # Собираем статистику за последние 7 дней
        start_date = current_date - timedelta(days=7)
        stats = stats_service.collect_stats_range(start_date, current_date)
        
        if not stats:
            logger.warning("Нет данных для отправки")
            return

        # Создаем изображение с командой недели
        image_path = image_service.create_team_image(stats)
        
        if not image_path or not os.path.exists(image_path):
            logger.error("Не удалось создать изображение команды")
            return

        # Отправляем изображение в Telegram
        caption = "🏒 Команда недели:\n\n"
        caption += "Лучшие игроки за последние 7 дней"
        
        if telegram_service.send_photo(image_path, caption):
            logger.info("Статистика успешно отправлена в Telegram")
        else:
            logger.error("Ошибка отправки статистики в Telegram")

    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 