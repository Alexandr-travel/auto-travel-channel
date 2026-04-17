import os
from dotenv import load_dotenv

# ✅ Сначала загружаем переменные окружения
load_dotenv()

# Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# TravelPayouts
TP_TOKEN = os.getenv('TRAVELPAYOUTS_API_KEY')
TP_MARKER = os.getenv('TP_MARKER', '')

# ✅ Проверка критичных переменных
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден! Добавьте переменную в Railway Variables")

if not CHANNEL_ID:
    raise ValueError("❌ CHANNEL_ID не найден! Добавьте переменную в Railway Variables")

# ✅ Фильтры туров (ОСЛАБЛЕНЫ для теста)
FILTERS = {
    'min_price': 5000,       # Минимальная цена (₽)
    'max_price': 300000,     # Максимальная цена (₽)
    'countries': [],         # Пустой список = ВСЕ страны
    'min_rating': 0,         # Минимальный рейтинг отеля (0 = любой)
    'nights_min': 2,         # Минимум ночей
    'nights_max': 30,        # Максимум ночей
}

# ✅ Расписание постинга (по UTC, Railway использует UTC)
SCHEDULE = {
    'morning': {'hour': 6, 'minute': 0},    # 09:00 МСК = 06:00 UTC
    'evening': {'hour': 16, 'minute': 30},  # 19:30 МСК = 16:30 UTC
    'weekend': {'hour': 9, 'minute': 0},    # 12:00 МСК = 09:00 UTC
}

# Настройки постов
POST_SETTINGS = {
    'max_posts_per_day': 4,      # Лимит постов в день
    'min_hours_between': 3,      # Минимум часов между постами
    'include_image': False,       # Картинки (False = стабильнее)
    'emoji_style': 'travel',      # 'travel' | 'fire' | 'minimal'
}

# Логирование
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')