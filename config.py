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

# ✅ Проверка критичных переменных
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден! Добавьте переменную в Railway Variables")

if not CHANNEL_ID:
    raise ValueError("❌ CHANNEL_ID не найден! Добавьте переменную в Railway Variables")

# ✅ ТЕСТОВЫЙ РЕЖИМ: используйте тестовые данные вместо реального API
# Установите TEST_MODE=true в Railway Variables для включения
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

# ✅ Фильтры предложений (работают и в тестовом режиме)
FILTERS = {
    'min_price': 5000,       # Минимальная цена (₽)
    'max_price': 300000,     # Максимальная цена (₽)
    'countries': [],         # Пустой список = ВСЕ направления
    'min_rating': 0,         # Любой рейтинг
    'nights_min': 2,         # Минимум ночей
    'nights_max': 30,        # Максимум ночей
}

# ✅ Расписание постинга (по UTC, Railway использует UTC)
# МСК = UTC + 3 часа
SCHEDULE = {
    'morning': {'hour': 6, 'minute': 0},    # 09:00 МСК
    'evening': {'hour': 16, 'minute': 30},  # 19:30 МСК
    'weekend': {'hour': 9, 'minute': 0},    # 12:00 МСК (сб/вс)
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