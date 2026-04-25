import asyncio
import logging
import os
import traceback
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command

# ✅ Импортируем ТОЛЬКО то, что есть в config.py
from config import SCHEDULE, POST_SETTINGS, LOG_LEVEL, CHANNEL_ID, FILTERS, TEST_MODE
from parser import FlightParser
from poster import ChannelPoster

# ✅ Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ✅ Глобальные переменные
parser = FlightParser()
poster = ChannelPoster()
last_post_time = None
posts_today = 0
last_reset_date = None
admin_bot: Bot = None

# ✅ Диспетчер и роутеры
dp = Dispatcher()
test_router = Router()

async def send_admin_alert(text: str, parse_mode: str = 'HTML'):
    """Уведомление админу в ЛС"""
    global admin_bot
    admin_id = os.getenv('ADMIN_ID')
    if not admin_id:
        return
    try:
        if admin_bot is None:
            admin_bot = Bot(token=os.getenv('BOT_TOKEN'))
        await admin_bot.send_message(
            chat_id=int(admin_id),
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.warning(f"⚠️ Не отправлено уведомление: {e}")

async def can_post() -> bool:
    """Можно ли публиковать пост"""
    global last_post_time, posts_today
    if posts_today >= POST_SETTINGS['max_posts_per_day']:
        return False
    if last_post_time:
        hours = (datetime.now() - last_post_time).total_seconds() / 3600
        if hours < POST_SETTINGS['min_hours_between']:
            return False
    return True

async def publish_flight():
    """Публикация одного авиабилета"""
    global last_post_time, posts_today
    if not await can_post():
        return
    try:
        flights = await parser.fetch_flights(limit=3)
        if not flights:
            logger.warning("❌ Нет доступных авиабилетов")
            return
        flight = flights[0]
        content = parser.format_flight_post(flight)
        success = await poster.post(content)
        if success:
            last_post_time = datetime.now()
            posts_today += 1
            logger.info(f"✅ Опубликован авиабилет #{posts_today}: {flight.get('origin')}→{flight.get('destination')}")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        await send_admin_alert(f"❌ Ошибка публикации:\n<code>{e}</code>")

async def morning_job():
    logger.info("🌅 Утренний постинг авиабилетов...")
    await publish_flight()

async def afternoon_job():
    logger.info("☀️ Дневной постинг авиабилетов...")
    await publish_flight()

async def evening_job():
    logger.info("🌆 Вечерний постинг авиабилетов...")
    await publish_flight()

async def setup_scheduler():
    """Настройка расписания"""
    scheduler = AsyncIOScheduler(timezone='UTC')
    scheduler.add_job(morning_job, CronTrigger(hour=SCHEDULE['morning']['hour'], minute=SCHEDULE['morning']['minute']), id='morning', name='Утро')
    scheduler.add_job(afternoon_job, CronTrigger(hour=SCHEDULE['afternoon']['hour'], minute=SCHEDULE['afternoon']['minute']), id='afternoon', name='День')
    scheduler.add_job(evening_job, CronTrigger(hour=SCHEDULE['evening']['hour'], minute=SCHEDULE['evening']['minute']), id='evening', name='Вечер')
    scheduler.start()
    # ✅ Показываем время в МСК (UTC+3)
    logger.info(f"⏰ Планировщик запущен. Посты: {SCHEDULE['morning']['hour']+3}:00, {SCHEDULE['afternoon']['hour']+3}:00, {SCHEDULE['evening']['hour']+3}:00 МСК")
    return scheduler

@test_router.message(Command("test"))
async def cmd_test(message: Message):
    """Тест по команде /test"""
    admin_id = os.getenv('ADMIN_ID')
    if admin_id and message.from_user.id != int(admin_id):
        await message.answer("❌ Доступ запрещён", parse_mode='HTML')
        return
    await message.answer("🔄 Тестовая публикация...", parse_mode='HTML')
    try:
        await publish_flight()
        await message.answer("✅ Готово!", parse_mode='HTML')
    except Exception as e:
        await message.answer(f"❌ Ошибка: <code>{e}</code>", parse_mode='HTML')

async def main():
    """Главная функция"""
    global last_post_time, posts_today, last_reset_date, admin_bot
    logger.info("✈️ Запуск авиа-бота...")
    logger.info(f"🧪 TEST_MODE: {TEST_MODE}")
    logger.info(f"📺 Канал: {CHANNEL_ID}")
    
    try:
        admin_bot = Bot(token=os.getenv('BOT_TOKEN'))
        await send_admin_alert(f"✅ <b>Авиа-бот запущен!</b>\n🕐 {datetime.now().strftime('%H:%M')} МСК")
        
        chat = await poster.bot.get_chat(CHANNEL_ID)
        logger.info(f"✅ Канал: {chat.title or CHANNEL_ID}")
        
        dp.include_router(test_router)
        scheduler = await setup_scheduler()
        
        logger.info("📡 Запуск polling...")
        await dp.start_polling(poster.bot)
        
    except KeyboardInterrupt:
        logger.info("⏹️ Остановка")
        await send_admin_alert("⏹️ Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        await send_admin_alert(f"❌ <b>БОТ УПАЛ!</b>\n<code>{e}</code>")
        raise
    finally:
        await parser.close()
        await poster.close()
        if admin_bot:
            await admin_bot.session.close()

if __name__ == "__main__":
    import sys
    sys.excepthook = lambda t, v, tb: logger.error(f"💥 {v}")
    asyncio.run(main())