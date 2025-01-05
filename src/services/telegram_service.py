import logging
from typing import Optional
from telegram import Bot
from telegram.error import TelegramError
from ..config import settings

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_TOKEN)
        self.chat_id = settings.TELEGRAM_CHAT_ID
        
    async def send_team_of_day(self, message: str, photo_path: Optional[str] = None) -> bool:
        """Отправляет сообщение с командой дня в Telegram"""
        try:
            if photo_path:
                with open(photo_path, 'rb') as photo:
                    await self.bot.send_photo(
                        chat_id=self.chat_id,
                        photo=photo,
                        caption=message,
                        parse_mode='Markdown'
                    )
            else:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                
            logger.info("Сообщение успешно отправлено в Telegram")
            return True
            
        except TelegramError as e:
            logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
            return False
            
    async def send_error(self, error_message: str) -> bool:
        """Отправляет сообщение об ошибке в Telegram"""
        try:
            message = f"❌ *Ошибка*\n\n{error_message}"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info("Сообщение об ошибке отправлено в Telegram")
            return True
            
        except TelegramError as e:
            logger.error(f"Ошибка при отправке сообщения об ошибке в Telegram: {e}")
            return False 