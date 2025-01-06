import logging
import os
from telegram import Bot
from telegram.constants import ParseMode
from dotenv import load_dotenv

class TelegramService:
    def __init__(self):
        """Инициализация сервиса Telegram"""
        load_dotenv()
        self.logger = logging.getLogger(__name__)
        
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('CHAT_ID')
        
        self.logger.info(f"Загружен токен бота: {'***' + self.token[-4:] if self.token else 'None'}")
        self.logger.info(f"Загружен ID чата: {self.chat_id}")
        
        if not self.token:
            raise ValueError("TELEGRAM_TOKEN не найден в переменных окружения")
        if not self.chat_id:
            raise ValueError("CHAT_ID не найден в переменных окружения")
            
        self.bot = Bot(token=self.token)

    async def send_photo(self, photo_path, caption=None):
        """Отправка фото в Telegram
        
        Args:
            photo_path (str): Путь к файлу изображения
            caption (str, optional): Подпись к фото
            
        Returns:
            bool: True если отправка успешна, False в противном случае
        """
        try:
            with open(photo_path, 'rb') as photo:
                await self.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            self.logger.info(f"Фото успешно отправлено: {photo_path}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при отправке фото: {e}")
            return False

    async def send_message(self, text):
        """Отправка текстового сообщения в Telegram
        
        Args:
            text (str): Текст сообщения
            
        Returns:
            bool: True если отправка успешна, False в противном случае
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=ParseMode.HTML
            )
            self.logger.info("Сообщение успешно отправлено")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при отправке сообщения: {e}")
            return False

    async def send_week_results(self, team, week_key, photo_path=None):
        """Отправка результатов недели
        
        Args:
            team (dict): Словарь с игроками по позициям
            week_key (str): Ключ недели
            photo_path (Path, optional): Путь к файлу коллажа
        """
        start_date, end_date = week_key.split('_')
        message = f"\U0001F3D2 Команда недели ({start_date} - {end_date})\n\n"
        
        for position, players in team.items():
            for player in players:
                message += f"{position}: {player['name']} ({player['total_points']:.2f} ftps)\n"

        if photo_path and await self.send_photo(photo_path):
            return
            
        # Если не удалось отправить фото или его нет, отправляем текст
        await self.send_message(message)
