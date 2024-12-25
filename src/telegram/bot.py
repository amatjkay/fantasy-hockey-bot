import logging
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from src.config.settings import load_env_vars

class TelegramService:
    def __init__(self):
        env_vars = load_env_vars()
        self.bot = Bot(token=env_vars['TELEGRAM_TOKEN'])
        self.chat_id = env_vars['CHAT_ID']
        self.max_attempts = 3
        self.retry_delay = 1

    async def send_photo(self, photo_path, caption=None):
        """Отправка фото в Telegram
        
        Args:
            photo_path (Path): Путь к файлу изображения
            caption (str, optional): Подпись к фото
            
        Returns:
            bool: True если отправка успешна, False в противном случае
        """
        for attempt in range(1, self.max_attempts + 1):
            try:
                with open(photo_path, 'rb') as photo:
                    await self.bot.send_photo(
                        chat_id=self.chat_id,
                        photo=photo,
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )
                logging.info(f"Фото успешно отправлено: {photo_path}")
                return True
            except Exception as e:
                if attempt < self.max_attempts:
                    logging.warning(f"Попытка {attempt} из {self.max_attempts} не удалась: {str(e)}")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logging.error(f"Не удалось отправить фото после {self.max_attempts} попыток: {str(e)}")
                    return False

    async def send_message(self, text):
        """Отправка текстового сообщения в Telegram
        
        Args:
            text (str): Текст сообщения
            
        Returns:
            bool: True если отправка успешна, False в противном случае
        """
        for attempt in range(1, self.max_attempts + 1):
            try:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=text,
                    parse_mode=ParseMode.HTML
                )
                logging.info("Сообщение успешно отправлено")
                return True
            except Exception as e:
                if attempt < self.max_attempts:
                    logging.warning(f"Попытка {attempt} из {self.max_attempts} не удалась: {str(e)}")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logging.error(f"Не удалось отправить сообщение после {self.max_attempts} попыток: {str(e)}")
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
            
        # Если не удалось отправить фо��о или его нет, отправляем текст
        await self.send_message(message)
