#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
from pathlib import Path
from services.telegram_service import TelegramService

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

# Читаем переменные окружения из файла .env
env_path = Path(__file__).parent.parent / '.env'
env_vars = {}
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()
            env_vars[key.strip()] = value.strip()

# Проверяем значения переменных
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')
logging.info(f"Загруженные переменные: TELEGRAM_BOT_TOKEN={bot_token}, TELEGRAM_CHAT_ID={chat_id}")

# Создаем экземпляр TelegramService и отправляем коллаж
try:
    service = TelegramService()
    service.send_team_of_the_day()
except Exception as e:
    logging.error(f"Ошибка при отправке коллажа: {e}") 