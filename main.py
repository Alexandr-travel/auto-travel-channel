import asyncio
import logging
import os
from datetime import datetime, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import SCHEDULE, POST_SETTINGS, LOG_LEVEL, CHANNEL_ID, FILTERS
from parser import TravelPayoutsParser
from poster import ChannelPoster

# ✅ Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ✅ Глобальные переменные (на уровне модуля)
parser = TravelPayoutsParser()
poster = ChannelPoster()
last_post_time = None
posts_today = 0
last_reset_date = None

async def can_post() -> bool:
    """Проверка, можно ли публиковать пост"""
    global last_post_time, posts_today
    
    if posts_today >= POST_SETTINGS['max_posts_per_day']:
        logger.info(f"❌ Лимит постов на сегодня исчерпан ({posts_today})")
        return False
    
    if last_post_time:
        hours_since = (datetime.now() - last_post_time).total_seconds() / 3600
        if hours_since < POST_SETTINGS['min_hours_between']:
            logger.info(f"⏳ Слишком рано для следующего поста ({hours_since:.1f}ч)")
            return False
    
    return True

async def publish_deal(post_type: str = 'tour'):
    """Публикация одного предложения"""
    global last_post_time, posts_today
    
    if not await can_post():
        return
    
    try:
        if post_type == 'tour':
            deals = await parser.fetch_hot_deals(limit=5)
            if not deals:
                logger.warning("❌ Нет доступных туров")
                return
            item = deals[0]
            content = parser.format_tour_post(item)
        else:
            flights = await parser.fetch_flight_deals(limit=3)
            if not flights:
                logger.warning("❌ Нет доступных авиабилетов")
                return
            item = flights[0]
            content = parser.format_flight_post(item)
        
        success = await poster.post(content)
        
        if success:
            last_post_time = datetime.now()
            posts_today += 1
            logger.info(f"✅ Опубликован {post_type} #{posts_today}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка публикации: {e}")

async def morning_job():
    """Утренний пост"""
    logger.info("🌅 Запуск утреннего постинга...")
    await publish_deal('tour')

async def evening_job():
    """Вечерний пост"""
    logger.info("🌆 Запуск вечернего постинга...")
    await publish_deal('tour')

async def weekend_job():
    """Пост в выходные"""
    logger.info("🎉 Запуск выходного постинга...")
    await publish_deal('tour')
    await asyncio.sleep(60)
    await publish_deal('flight')

async def setup_scheduler():
    """Настройка расписания"""
    scheduler = AsyncIOScheduler(timezone='UTC')
    
    scheduler.add_job(
        morning_job,
        CronTrigger(hour=SCHEDULE['morning']['hour'], minute=SCHEDULE['morning']['minute']),
        id='morning',
        name='Утренний пост'
    )
    
    scheduler.add_job(
        evening_job,
        CronTrigger(hour=SCHEDULE['evening']['hour'], minute=SCHEDULE['evening']['minute']),
        id='evening',
        name='Вечерний пост'
    )
    
    scheduler.add_job(
        weekend_job,
        CronTrigger(hour=SCHEDULE['weekend']['hour'], minute=SCHEDULE['weekend']['minute'], day_of_week='sat,sun'),
        id='weekend',
        name='Выходной пост'
    )
    
    scheduler.start()
    logger.info(f"⏰ Планировщик запущен. Следующие посты:")
    for job in scheduler.get_jobs():
        logger.info(f"   • {job.name}: {job.next_run_time}")
    
    return scheduler

async def main():
    """Главная функция"""
    # ✅ global в САМОМ НАЧАЛЕ функции, до любого использования!
    global posts_today, last_reset_date, last_post_time
    
    logger.info("🚀 Запуск авто-канала туров...")
    
    try:
        # Проверка подключения к каналу
        chat = await poster.bot.get_chat(CHANNEL_ID)
        logger.info(f"✅ Подключен к каналу: {chat.title or CHANNEL_ID}")
        
        # Запускаем планировщик
        scheduler = await setup_scheduler()
        
        # Основной цикл
        while True:
            await asyncio.sleep(60)
            
            # Сброс счётчика 1 раз в сутки в 00:00 UTC
            today = datetime.now().date()
            if today != last_reset_date and datetime.now().hour == 0:
                posts_today = 0
                last_reset_date = today
                logger.info(f"🔄 Счётчик постов сброшен ({today})")
                
    except KeyboardInterrupt:
        logger.info("⏹️ Остановка по запросу пользователя")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise
    finally:
        await parser.close()
        await poster.close()
        logger.info("👋 Сессии закрыты")

if __name__ == "__main__":
    asyncio.run(main())