import asyncio
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from config import BOT_TOKEN, CHANNEL_ID

class ChannelPoster:
    """Отправка постов в Telegram канал"""
    
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
    
    async def close(self):
        await self.bot.session.close()
    
    async def post(self, content: dict) -> bool:
        """Публикация поста в канале"""
        try:
            if content.get('image'):
                # Пост с картинкой
                await self.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=content['image'],
                    caption=content['text'],
                    parse_mode=content.get('parse_mode', 'HTML')
                )
            else:
                # Текстовый пост
                await self.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=content['text'],
                    parse_mode=content.get('parse_mode', 'HTML'),
                    disable_web_page_preview=False
                )
            print(f"✅ Пост опубликован: {content.get('link', 'no link')[:50]}...")
            return True
            
        except TelegramBadRequest as e:
            print(f"❌ Ошибка Telegram: {e}")
            return False
        except Exception as e:
            print(f"❌ Ошибка публикации: {type(e).__name__}: {e}")
            return False
    
    async def post_with_buttons(self, content: dict, buttons: list) -> bool:
        """Пост с инлайн-кнопками"""
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=btn['text'], url=btn['url'])]
            for btn in buttons
        ])
        
        try:
            if content.get('image'):
                await self.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=content['image'],
                    caption=content['text'],
                    parse_mode=content.get('parse_mode', 'HTML'),
                    reply_markup=keyboard
                )
            else:
                await self.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=content['text'],
                    parse_mode=content.get('parse_mode', 'HTML'),
                    reply_markup=keyboard
                )
            return True
        except Exception as e:
            print(f"❌ Ошибка поста с кнопками: {e}")
            return False