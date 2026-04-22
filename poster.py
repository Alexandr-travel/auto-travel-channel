import os
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class ChannelPoster:
    """Отправка постов в Telegram канал"""
    
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        if not self.token:
            raise ValueError("❌ BOT_TOKEN не найден!")
        
        logger.info(f"✅ BOT_TOKEN загружен (длина: {len(self.token)} символов)")
        self.bot = Bot(token=self.token)
        logger.info("✅ Bot объект создан")
    
    async def close(self):
        await self.bot.session.close()
        logger.info("👋 Сессия бота закрыта")
    
    async def post(self, content: dict) -> bool:
        """Публикация поста в канале"""
        try:
            if content.get('image'):
                await self.bot.send_photo(
                    chat_id=os.getenv('CHANNEL_ID'),
                    photo=content['image'],
                    caption=content['text'],
                    parse_mode=content.get('parse_mode', 'HTML')
                )
            else:
                await self.bot.send_message(
                    chat_id=os.getenv('CHANNEL_ID'),
                    text=content['text'],
                    parse_mode=content.get('parse_mode', 'HTML'),
                    disable_web_page_preview=False
                )
            logger.info(f"✅ Пост опубликован")
            return True
        except TelegramBadRequest as e:
            logger.error(f"❌ Ошибка Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка публикации: {type(e).__name__}: {e}")
            return False