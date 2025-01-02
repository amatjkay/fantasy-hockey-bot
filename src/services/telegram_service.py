import os
import logging
import requests
from dotenv import load_dotenv

class TelegramService:
    def __init__(self):
        # Загружаем переменные окружения
        load_dotenv()
        
        # Получаем значения из переменных окружения
        self.bot_token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            raise ValueError("TELEGRAM_TOKEN и CHAT_ID должны быть установлены в переменных окружения")
        
        logging.info(f"Bot token: {self.bot_token}")
        logging.info(f"Chat ID: {self.chat_id}")
        
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_team_of_the_day(self):
        """Отправляет коллаж команды дня в Telegram"""
        try:
            image_path = 'data/output/team_collage.png'
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Файл коллажа не найден по пути: {image_path}")
            
            url = f"{self.api_url}/sendPhoto"
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {'chat_id': self.chat_id}
                response = requests.post(url, files=files, data=data)
                response.raise_for_status()
            
            logging.info("Коллаж успешно отправлен в Telegram")
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при отправке сообщения в Telegram: {e}")
            raise
        except Exception as e:
            logging.error(f"Неожиданная ошибка: {e}")
            raise 