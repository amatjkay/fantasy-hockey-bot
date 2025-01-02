#!/usr/bin/env python3

import os
import sys
import logging
from dotenv import load_dotenv
from pathlib import Path

# Добавляем путь к src в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from src.services.telegram_service import TelegramService

def main():
    # Настраиваем логирование
    logging.basicConfig(level=logging.INFO)
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Проверяем значения переменных окружения
    bot_token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    logging.info(f"Bot token: {bot_token}")
    logging.info(f"Chat ID: {chat_id}")
    
    try:
        # Создаем экземпляр TelegramService
        telegram_service = TelegramService()
        
        # Отправляем коллаж
        telegram_service.send_team_of_the_day()
    except Exception as e:
        logging.error(f"Ошибка при отправке коллажа: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 