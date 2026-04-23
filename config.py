import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
ADMIN_ID = os.getenv('ADMIN_ID')

# TravelPayouts
TP_TOKEN = os.getenv('TRAVELPAYOUTS_API_KEY')
TP_MARKER = os.getenv('TP_MARKER', '')

# ✅ ТЕСТОВЫЙ РЕЖИМ
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

# ✅ Проверка критичных переменных
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден!")
if not CHANNEL_ID:
    raise ValueError("❌ CHANNEL_ID не найден!")

# Фильтры
FILTERS = {
    'min_price': 5000,
    'max_price': 300000,
    'countries': [],
    'min_rating': 0,
    'nights_min': 2,
    'nights_max': 30,
}

# Расписание (UTC)
SCHEDULE = {
    'morning': {'hour': 6, 'minute': 0},    # 09:00 МСК
    'evening': {'hour': 16, 'minute': 30},  # 19:30 МСК
    'weekend': {'hour': 9, 'minute': 0},    # 12:00 МСК
}

# Настройки постов
POST_SETTINGS = {
    'max_posts_per_day': 4,
    'min_hours_between': 3,
    'include_image': False,
    'emoji_style': 'travel',
}

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')