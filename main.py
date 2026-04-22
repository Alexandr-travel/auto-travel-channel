import asyncio
import logging
import os
import traceback
from datetime import datetime, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from aiogram import Bot, Router
from aiogram.types import Message
from aiogram.filters import Command

from config import SCHEDULE, POST_SETTINGS, LOG_LEVEL, CHANNEL_ID, FILTERS, TEST_MODE
from parser import TravelPayoutsParser
from poster import ChannelPoster

# ✅ Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ✅ Глобальные переменные
parser = TravelPayoutsParser()
poster = ChannelPoster()
last_post_time = None
posts_today = 0
last_reset_date = None
admin_bot: Bot = None

async def send_admin_alert(text: str, parse_mode: str = 'HTML'):
    """Отправка уведомления админу в ЛС"""
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
        logger.info(f"🔔 Уведомление отправлено админу")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось отправить уведомление: {e}")

async def can_post() -> bool:
    """Проверка, можно ли публиковать пост"""
    global last_post_time, posts_today
    
    if posts_today >= POST_SETTINGS['max_posts_per_day']:
        logger.info(f"❌ Лимит постов исчерпан ({posts_today})")
        return False
    
    if last_post_time:
        hours_since = (datetime.now() - last_post_time).total_seconds() / 3600
        if hours_since < POST_SETTINGS['min_hours_between']:
            return False
    
    return True

async def publish_deal(post_type: str = 'tour'):
    """Публикация одного предложения"""
    global last_post_time, posts_today
    
    if not await can_post():
        return
    
    try:
        deals = await parser.fetch_hot_deals(limit=5)
        if not deals:
            logger.warning("❌ Нет доступных предложений")
            return
        
        item = deals[0]
        content = parser.format_tour_post(item)
        success = await poster.post(content)
        
        if success:
            last_post_time = datetime.now()
            posts_today += 1
            logger.info(f"✅ Опубликован {post_type} #{posts_today}")
            
    except Exception as e:
        error_msg = f"❌ Ошибка публикации: {type(e).__name__}: {e}"
        logger.error(error_msg)
        await send_admin_alert(f"❌ Ошибка публикации:\n<code>{error_msg}</code>")

async def morning_job():
    logger.info("🌅 Запуск утреннего постинга...")
    await publish_deal('tour')

async def evening_job():
    logger.info("🌆 Запуск вечернего постинга...")
    await publish_deal('tour')

async def weekend_job():
    logger.info("🎉 Запуск выходного постинга...")
    await publish_deal('tour')
    await asyncio.sleep(60)
    await publish_deal('flight')

async def setup_scheduler():
    """Настройка расписания"""
    scheduler = AsyncIOScheduler(timezone='UTC')
    
    scheduler.add_job(morning_job, CronTrigger(hour=SCHEDULE['morning']['hour'], minute=SCHEDULE['morning']['minute']), id='morning', name='Утренний пост')
    scheduler.add_job(evening_job, CronTrigger(hour=SCHEDULE['evening']['hour'], minute=SCHEDULE['evening']['minute']), id='evening', name='Вечерний пост')
    scheduler.add_job(weekend_job, CronTrigger(hour=SCHEDULE['weekend']['hour'], minute=SCHEDULE['weekend']['minute'], day_of_week='sat,sun'), id='weekend', name='Выходной пост')
    
    scheduler.start()
    logger.info(f"⏰ Планировщик запущен. Следующие посты:")
    for job in scheduler.get_jobs():
        logger.info(f"   • {job.name}: {job.next_run_time}")
    return scheduler

async def cmd_test(message: Message):
    """Тестовая публикация по команде /test"""
    admin_id = os.getenv('ADMIN_ID')
    if admin_id and message.from_user.id != int(admin_id):
        await message.answer("❌ Доступ запрещён", parse_mode='HTML')
        return
    
    await message.answer("🔄 Запускаю тестовую публикацию...", parse_mode='HTML')
    try:
        await publish_deal('tour')
        await message.answer("✅ Готово! Проверьте канал.", parse_mode='HTML')
    except Exception as e:
        await message.answer(f"❌ Ошибка: <code>{e}</code>", parse_mode='HTML')

async def main():
    """Главная функция"""
    global posts_today, last_reset_date, last_post_time, admin_bot
    
    logger.info("🚀 Запуск авто-канала туров...")
    logger.info(f"🧪 TEST_MODE: {TEST_MODE}")
    
    try:
        admin_bot = Bot(token=os.getenv('BOT_TOKEN'))
        await send_admin_alert("✅ <b>Бот запущен!</b>\n🕐 " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + f"\n🧪 TEST_MODE: {TEST_MODE}")
        
        chat = await poster.bot.get_chat(CHANNEL_ID)
        logger.info(f"✅ Подключен к каналу: {chat.title or CHANNEL_ID}")
        
        scheduler = await setup_scheduler()
        
        # Регистрируем хендлер /test
        test_router = Router()
        test_router.message(Command("test"))(cmd_test)
        # Если используете основной dispatcher — добавьте тест-роутер туда
        
        while True:
            await asyncio.sleep(60)
            today = datetime.now().date()
            if today != last_reset_date and datetime.now().hour == 0:
                posts_today = 0
                last_reset_date = today
                logger.info(f"🔄 Счётчик постов сброшен ({today})")
                
    except KeyboardInterrupt:
        logger.info("⏹️ Остановка по запросу")
        await send_admin_alert("⏹️ Бот остановлен вручную")
    except Exception as e:
        error_msg = f"❌ Критическая ошибка: {type(e).__name__}: {e}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        await send_admin_alert(f"❌ <b>БОТ УПАЛ!</b>\n\n<code>{error_msg}</code>")
        raise
    finally:
        try:
            await parser.close()
            await poster.close()
            if admin_bot:
                await admin_bot.session.close()
            logger.info("👋 Сессии закрыты")
        except:
            pass

if __name__ == "__main__":
    def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            return
        error_msg = f"💥 Uncaught: {exc_type.__name__}: {exc_value}"
        logger.error(error_msg)
        try:
            asyncio.run(send_admin_alert(f"💥 <b>КРАХ!</b>\n<code>{error_msg}</code>"))
        except:
            pass
    
    import sys
    sys.excepthook = handle_uncaught_exception
    asyncio.run(main())