import os
from dotenv import load_dotenv

# ✅ Сначала загружаем переменные окружения
load_dotenv()

# Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
ADMIN_ID = os.getenv('ADMIN_ID')

# TravelPayouts
TP_TOKEN = os.getenv('TRAVELPAYOUTS_API_KEY')
TP_MARKER = os.getenv('TP_MARKER', '')

# ✅ Ваш партнёрский ID в TravelPayouts (ОБЯЗАТЕЛЬНО замените на актуальный!)
# Найдите его в кабинете: app.travelpayouts.com → профиль или настройки
TP_PARTNER_ID = os.getenv('TP_PARTNER_ID', '713263')

# ✅ Проверка критичных переменных
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден! Добавьте переменную в Railway Variables")

if not CHANNEL_ID:
    raise ValueError("❌ CHANNEL_ID не найден! Добавьте переменную в Railway Variables")

if not TP_PARTNER_ID:
    raise ValueError("❌ TP_PARTNER_ID не найден! Добавьте ваш ID партнёра в Variables")

# ✅ ТЕСТОВЫЙ РЕЖИМ: используйте тестовые данные вместо реального API
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

# ✅ Фильтры предложений
FILTERS = {
    'min_price': 5000,
    'max_price': 300000,
    'countries': [],
    'min_rating': 0,
    'nights_min': 2,
    'nights_max': 30,
}

# ✅ Расписание постинга (по UTC)
SCHEDULE = {
    'morning': {'hour': 6, 'minute': 0},    # 09:00 МСК
    'evening': {'hour': 16, 'minute': 30},  # 19:30 МСК
    'weekend': {'hour': 9, 'minute': 0},    # 12:00 МСК (сб/вс)
}

# Настройки постов
POST_SETTINGS = {
    'max_posts_per_day': 4,
    'min_hours_between': 3,
    'include_image': False,
    'emoji_style': 'travel',
}

# Логирование
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')