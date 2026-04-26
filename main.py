import asyncio
import logging
import os
import traceback
import sys
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command

from config import SCHEDULE, POST_SETTINGS, LOG_LEVEL, CHANNEL_ID, FILTERS, TEST_MODE
from parser import FlightParser
from poster import ChannelPoster

# ✅ Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
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
        hours = (datetime.now() - last_post_time).total_seconds() / 3600
        if hours < POST_SETTINGS['min_hours_between']:
            logger.info(f"⏳ Слишком рано для следующего поста ({hours:.1f}ч)")
            return False
    return True


async def publish_flight():
    """Публикация поста с несколькими вариантами рейсов (чартер-формат)"""
    global last_post_time, posts_today
    
    if not await can_post():
        return
    
    try:
        # ✅ Запрашиваем несколько рейсов для одного поста
        flights = await parser.fetch_flights(limit=5)
        if not flights:
            logger.warning("❌ Нет доступных авиабилетов")
            return
        
        # ✅ Форматируем ВСЕ рейсы в один пост
        content = parser.format_flight_post(flights)
        success = await poster.post(content)
        
        if success:
            last_post_time = datetime.now()
            posts_today += 1
            
            # ✅ БЕЗОПАСНОЕ получение направления
            try:
                first = flights[0] if flights else {}
                if isinstance(first, dict):
                    direction = f"{first.get('origin', '?')}→{first.get('destination', '?')}"
                else:
                    direction = "???"
            except:
                direction = "???"
            
            logger.info(f"✅ Опубликован чартер-пост #{posts_today}: {direction}")
            
    except Exception as e:
        error_msg = f"❌ Ошибка публикации: {type(e).__name__}: {e}"
        logger.error(error_msg)
        await send_admin_alert(f"❌ Ошибка публикации:\n<code>{error_msg}</code>")


async def morning_job():
    """Утренний постинг"""
    logger.info("🌅 Утренний постинг авиабилетов...")
    await publish_flight()


async def afternoon_job():
    """Дневной постинг"""
    logger.info("☀️ Дневной постинг авиабилетов...")
    await publish_flight()


async def evening_job():
    """Вечерний постинг"""
    logger.info("🌆 Вечерний постинг авиабилетов...")
    await publish_flight()


async def setup_scheduler():
    """Настройка расписания постинга"""
    scheduler = AsyncIOScheduler(timezone='UTC')
    
    scheduler.add_job(
        morning_job,
        CronTrigger(hour=SCHEDULE['morning']['hour'], minute=SCHEDULE['morning']['minute']),
        id='morning',
        name='Утро'
    )
    scheduler.add_job(
        afternoon_job,
        CronTrigger(hour=SCHEDULE['afternoon']['hour'], minute=SCHEDULE['afternoon']['minute']),
        id='afternoon',
        name='День'
    )
    scheduler.add_job(
        evening_job,
        CronTrigger(hour=SCHEDULE['evening']['hour'], minute=SCHEDULE['evening']['minute']),
        id='evening',
        name='Вечер'
    )
    
    scheduler.start()
    
    msk_times = [
        f"{SCHEDULE['morning']['hour']+3}:00",
        f"{SCHEDULE['afternoon']['hour']+3}:00", 
        f"{SCHEDULE['evening']['hour']+3}:00"
    ]
    logger.info(f"⏰ Планировщик запущен. Посты: {', '.join(msk_times)} МСК")
    
    return scheduler


@test_router.message(Command("test"))
async def cmd_test(message: Message):
    """Тестовая публикация по команде /test"""
    admin_id = os.getenv('ADMIN_ID')
    
    if admin_id:
        if message.from_user.id != int(admin_id):
            await message.answer("❌ Доступ запрещён", parse_mode='HTML')
            return
    
    await message.answer("🔄 Запускаю тестовую публикацию...", parse_mode='HTML')
    
    try:
        await publish_flight()
        await message.answer("✅ Готово! Проверьте канал.", parse_mode='HTML')
    except Exception as e:
        await message.answer(f"❌ Ошибка: <code>{e}</code>", parse_mode='HTML')
        await send_admin_alert(f"❌ Ошибка при тесте: <code>{e}</code>")


async def main():
    """Главная функция запуска бота"""
    global last_post_time, posts_today, last_reset_date, admin_bot
    
    logger.info("✈️ Запуск авиа-бота (Москва ↔ Нячанг)...")
    logger.info(f"🧪 TEST_MODE: {TEST_MODE}")
    logger.info(f"📺 Канал: {CHANNEL_ID}")
    
    try:
        admin_bot = Bot(token=os.getenv('BOT_TOKEN'))
        
        startup_info = (
            f"✅ <b>Авиа-бот запущен!</b>\n"
            f"🕐 {datetime.now().strftime('%H:%M')} МСК\n"
            f"🏖️ Направление: Москва ↔ Нячанг"
        )
        await send_admin_alert(startup_info)
        
        chat = await poster.bot.get_chat(CHANNEL_ID)
        logger.info(f"✅ Канал: {chat.title or CHANNEL_ID}")
        
        dp.include_router(test_router)
        logger.info("✅ Хендлер /test зарегистрирован")
        
        scheduler = await setup_scheduler()
        
        logger.info("📡 Запуск polling...")
        await dp.start_polling(poster.bot)
        
    except KeyboardInterrupt:
        logger.info("⏹️ Остановка по запросу пользователя")
        await send_admin_alert("⏹️ Бот остановлен вручную")
        
    except Exception as e:
        error_msg = f"❌ Критическая ошибка: {type(e).__name__}: {e}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        await send_admin_alert(
            f"❌ <b>БОТ УПАЛ!</b>\n\n"
            f"<code>{error_msg}</code>\n\n"
            f"<code>{traceback.format_exc()[:1000]}</code>"
        )
        raise
        
    finally:
        try:
            await parser.close()
            await poster.close()
            if admin_bot:
                await admin_bot.session.close()
            logger.info("👋 Сессии закрыты")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при закрытии сессий: {e}")


if __name__ == "__main__":
    def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            return
        error_msg = f"💥 Uncaught exception: {exc_type.__name__}: {exc_value}"
        logger.error(error_msg)
        logger.error(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        try:
            asyncio.run(send_admin_alert(f"💥 <b>КРАХ БОТА!</b>\n<code>{error_msg}</code>"))
        except:
            pass
    
    sys.excepthook = handle_uncaught_exception
    
    asyncio.run(main())