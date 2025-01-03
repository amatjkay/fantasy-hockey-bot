import os
import logging
import requests
from typing import Optional
from config import (
    setup_logging,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    OUTPUT_DIR
)

class TelegramService:
    """Сервис для отправки сообщений и изображений в Telegram"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.logger = setup_logging('telegram')
        
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            raise ValueError("TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID должны быть установлены в конфигурации")
        
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
    def send_team_of_the_day(self, image_path: Optional[str] = None) -> bool:
        """Отправляет коллаж команды дня в Telegram
        
        Args:
            image_path (str, optional): Путь к изображению коллажа
            
        Returns:
            bool: True если сообщение успешно отправлено, False в случае ошибки
        """
        try:
            if image_path is None:
                image_path = os.path.join(OUTPUT_DIR, 'team_collage.jpg')
                
            if not os.path.exists(image_path):
                self.logger.error(f"Файл коллажа не найден: {image_path}")
                return False
            
            url = f"{self.api_url}/sendPhoto"
            
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {'chat_id': self.chat_id}
                
                for attempt in range(3):  # 3 попытки отправки
                    try:
                        response = requests.post(url, files=files, data=data, timeout=30)
                        response.raise_for_status()
                        self.logger.info("Коллаж успешно отправлен в Telegram")
                        return True
                    except requests.exceptions.RequestException as e:
                        if attempt == 2:  # Последняя попытка
                            self.logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
                            return False
                        continue
            
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при отправке сообщения: {e}")
            return False
            
    def send_team_of_the_week(self, image_path: Optional[str] = None) -> bool:
        """Отправляет коллаж команды недели в Telegram
        
        Args:
            image_path (str, optional): Путь к изображению коллажа
            
        Returns:
            bool: True если сообщение успешно отправлено, False в случае ошибки
        """
        try:
            if image_path is None:
                image_path = os.path.join(OUTPUT_DIR, 'week_team_collage.jpg')
                
            if not os.path.exists(image_path):
                self.logger.error(f"Файл коллажа не найден: {image_path}")
                return False
            
            url = f"{self.api_url}/sendPhoto"
            
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {'chat_id': self.chat_id}
                
                for attempt in range(3):  # 3 попытки отправки
                    try:
                        response = requests.post(url, files=files, data=data, timeout=30)
                        response.raise_for_status()
                        self.logger.info("Коллаж команды недели успешно отправлен в Telegram")
                        return True
                    except requests.exceptions.RequestException as e:
                        if attempt == 2:  # Последняя попытка
                            self.logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
                            return False
                        continue
            
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при отправке сообщения: {e}")
            return False 